"""
iterative_context_optimization.py

Fitting documents to a budget isn't a one-shot decision -- it's an
iterative process: start with the best candidates, keep adding more
while budget allows, and when something doesn't fit, try summarizing it
down instead of just dropping it. Each step is measured, not assumed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context_budget_calculator import estimate_tokens
from summarization_techniques import extractive_summarize


CANDIDATES = [
    {"title": "RAG overview", "text": "RAG retrieves documents before generating an answer, grounding responses in real sources instead of pure memorized knowledge. " * 3, "similarity": 0.95},
    {"title": "Why RAG matters", "text": "RAG matters because language models can be outdated. Retrieval lets them use fresh, specific information without needing to be retrained. " * 4, "similarity": 0.85},
    {"title": "Vector databases", "text": "A vector database stores embeddings and allows fast similarity search across large document collections, often using approximate indexing. " * 5, "similarity": 0.70},
    {"title": "Chunking", "text": "Chunking splits documents into smaller pieces so they fit well in embeddings and retrieval, respecting natural boundaries like sentences and paragraphs. " * 4, "similarity": 0.55},
]


def iterative_fit(candidates, token_budget, summarize_threshold_ratio=0.6):
    """
    ITERATIVE OPTIMIZATION:
      1. Sort candidates best-first (relevance).
      2. Walk down the list, adding each one if it fits as-is.
      3. If a candidate DOESN'T fit, but summarizing it would get it
         under budget AND it's still reasonably relevant (similarity
         above a floor), summarize it and add the summary instead of
         just dropping it.
      4. Stop once budget runs out or candidates run out.

    This models a real selection process more honestly than a single
    greedy pass: "doesn't fit as-is" and "not worth including at all"
    are different situations, and treating them the same wastes
    potentially useful information.
    """
    ranked = sorted(candidates, key=lambda c: c["similarity"], reverse=True)
    selected = []
    used_tokens = 0
    steps = []

    for candidate in ranked:
        full_cost = estimate_tokens(candidate["text"])
        remaining = token_budget - used_tokens

        if full_cost <= remaining:
            selected.append({**candidate, "text": candidate["text"], "was_summarized": False})
            used_tokens += full_cost
            steps.append(f"ADDED as-is: \"{candidate['title']}\" ({full_cost} tokens, {remaining - full_cost} remaining)")
            continue

        # Doesn't fit as-is -- try summarizing it down.
        summary = extractive_summarize(candidate["text"], max_sentences=1)
        summary_cost = estimate_tokens(summary)

        if summary_cost <= remaining:
            selected.append({**candidate, "text": summary, "was_summarized": True})
            used_tokens += summary_cost
            steps.append(
                f"SUMMARIZED to fit: \"{candidate['title']}\" "
                f"({full_cost} -> {summary_cost} tokens, {remaining - summary_cost} remaining)"
            )
        else:
            steps.append(
                f"DROPPED: \"{candidate['title']}\" (needs {full_cost} tokens full, "
                f"{summary_cost} even summarized -- only {remaining} tokens left)"
            )

    return selected, used_tokens, steps


def main():
    print("=== Iterative Context Optimization ===\n")

    for token_budget in [120, 220, 400]:
        print(f"--- Budget: {token_budget} tokens ---\n")
        selected, used, steps = iterative_fit(CANDIDATES, token_budget)

        for step in steps:
            print(f"  {step}")

        print(f"\n  Final: {len(selected)} document(s), {used}/{token_budget} tokens used")
        for doc in selected:
            marker = " (summarized)" if doc["was_summarized"] else ""
            print(f"    - {doc['title']}{marker}")
        print()

    print(
        "Why iterate instead of a single pass: a document that doesn't fit "
        "in full might still be worth a shortened version, especially if "
        "it's highly relevant -- dropping it entirely loses that "
        "information completely, when a 1-sentence summary could have "
        "preserved the core point for a fraction of the token cost. "
        "The strategy at each step: try full first (highest fidelity), "
        "fall back to summarized (partial fidelity, still something), "
        "and only drop entirely when neither fits."
    )


if __name__ == "__main__":
    main()
