"""
multi_turn_strategy.py

When even the best single-call selection strategy can't fit everything
genuinely needed to answer a question well, one option is to NOT answer
in one call: break the work into multiple turns, each handling a subset
of the material, carrying forward only a running summary (not the full
text) between turns.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context_budget_calculator import estimate_tokens
from summarization_techniques import extractive_summarize


def chunk_candidates_into_turns(candidates, tokens_per_turn):
    """
    Splits a large candidate pool into groups that each fit within a
    per-turn token budget, greedily filling each turn before starting
    the next one.
    """
    turns = []
    current_turn = []
    current_tokens = 0

    for candidate in candidates:
        cost = estimate_tokens(candidate["text"])
        if current_turn and current_tokens + cost > tokens_per_turn:
            turns.append(current_turn)
            current_turn = []
            current_tokens = 0
        current_turn.append(candidate)
        current_tokens += cost

    if current_turn:
        turns.append(current_turn)

    return turns


def simulate_turn_answer(turn_documents, running_summary, query):
    """
    Stands in for an actual LLM call: in a real system, this would send
    the query, the running summary of prior turns, and this turn's
    documents to the model and get back a partial answer. We simulate
    that with a template so the FLOW is visible without needing a real
    API call.
    """
    titles = [d["title"] for d in turn_documents]
    return f"[Partial answer using {', '.join(titles)}, building on prior context: \"{running_summary[:40]}...\" if any]"


def update_running_summary(running_summary, new_turn_documents, max_summary_tokens=60):
    """
    MAINTAIN CONTEXT ACROSS TURNS: instead of carrying the full text of
    every prior turn forward (which would just recreate the original
    context-limit problem), we carry forward a SUMMARY that gets
    re-compressed each turn to stay within a fixed budget. This is the
    key design choice that makes multi-turn actually work: what persists
    between turns is bounded, not ever-growing.
    """
    combined_text = running_summary + " " + " ".join(d["text"] for d in new_turn_documents)
    new_summary = extractive_summarize(combined_text, max_sentences=2)

    # If even the 2-sentence summary is still too big, fall back to 1.
    if estimate_tokens(new_summary) > max_summary_tokens:
        new_summary = extractive_summarize(combined_text, max_sentences=1)

    return new_summary


# Each document has real, VARIED sentences (not a single sentence
# repeated), so the extractive summarizer has genuinely different
# material to choose from -- repeating one sentence would make every
# "summary" just that one sentence duplicated, which both looks wrong
# and (more importantly) crowds out the running summary from prior turns.
DOCUMENTS = [
    {"title": "RAG overview", "text": "RAG retrieves documents before generating an answer. It grounds responses in real sources instead of pure memorized knowledge. This reduces the risk of confidently wrong answers."},
    {"title": "Why RAG matters", "text": "RAG matters because language models can be outdated. Retrieval lets them use fresh information without retraining. It also lets a model answer using private data it never saw during training."},
    {"title": "Vector databases", "text": "A vector database stores embeddings for fast similarity search. It allows finding documents with similar meaning, not just matching keywords. Real vector databases use indexing to stay fast at scale."},
    {"title": "Chunking", "text": "Chunking splits documents into smaller pieces. This helps them fit well in embeddings and retrieval. Good chunking respects natural boundaries like sentences and paragraphs."},
    {"title": "Ranking", "text": "Ranking combines similarity with other signals. Recency and quality can matter as much as topical match. The best ranking order depends on what the user actually needs."},
    {"title": "Generation", "text": "Generation uses retrieved and ranked context to produce an answer. It should cite which sources support each claim. A good generator says when it doesn't have enough information."},
]


def run_multi_turn_conversation(documents, query, tokens_per_turn):
    turns = chunk_candidates_into_turns(documents, tokens_per_turn)

    print(f"Query: \"{query}\"")
    print(f"Per-turn budget: {tokens_per_turn} tokens -> split into {len(turns)} turn(s)\n")

    running_summary = ""
    for i, turn_docs in enumerate(turns, start=1):
        turn_tokens = sum(estimate_tokens(d["text"]) for d in turn_docs)
        titles = [d["title"] for d in turn_docs]
        print(f"Turn {i}: {len(turn_docs)} document(s) ({turn_tokens} tokens) -- {titles}")

        answer = simulate_turn_answer(turn_docs, running_summary, query)
        print(f"  {answer}")

        running_summary = update_running_summary(running_summary, turn_docs)
        print(f"  Running summary carried forward ({estimate_tokens(running_summary)} tokens): \"{running_summary}\"\n")

    print(f"Final running summary after all turns: \"{running_summary}\"")
    return running_summary


def main():
    print("=== Multi-Turn Strategy ===\n")

    run_multi_turn_conversation(DOCUMENTS, "Explain the full RAG pipeline end to end.", tokens_per_turn=60)

    print("\n" + "=" * 60)
    print(
        "\nWorth being honest about a real limitation visible above: look "
        "closely and the running summary sometimes stays IDENTICAL across "
        "several turns (e.g. after 'Vector databases' and 'Chunking'). "
        "That's our extractive summarizer picking the same two highest-"
        "scoring sentences from EARLIER turns again, because their words "
        "happen to overlap with the combined text's overall vocabulary --"
        " which means that turn's new content got silently dropped from "
        "what's carried forward, not blended in like intended. A real "
        "production system would need a genuinely abstractive summarizer "
        "(an actual LLM call) to reliably fold NEW information into a "
        "running summary; naive extractive re-scoring can get stuck "
        "favoring old content. This is a good example of why 'maintain "
        "context across turns' is a harder problem than it first looks.\n"
    )
    print(
        "Multi-turn design notes:\n"
        "- What's carried forward between turns is a bounded SUMMARY, not "
        "the raw text of every prior turn -- otherwise turn 10 would need "
        "to fit everything from turns 1-9 PLUS its own new material, "
        "recreating the exact problem multi-turn exists to avoid.\n"
        "- Each turn's partial answer can be shown to the user incrementally "
        "(useful for a long, complex question) or collected and only the "
        "FINAL turn's answer shown, depending on the use case.\n"
        "- The real cost: more LLM calls (more latency, more cost per "
        "question) and a harder prompt-engineering problem (asking the "
        "model to build on a summary instead of the original text). "
        "Multi-turn is a genuine way to bypass a hard context limit, not "
        "a free one -- worth reaching for when a single call truly can't "
        "fit what's needed, not as a default strategy."
    )


if __name__ == "__main__":
    main()
