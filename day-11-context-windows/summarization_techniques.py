"""
summarization_techniques.py

Three ways to compress a document so it costs fewer tokens: extractive
(pull out existing sentences), abstractive-style (rewrite shorter,
simulated via a template since we don't call a real LLM), and key-point
extraction (bullet points). Each is measured for compression ratio and
a simple grounding check so "shorter" doesn't quietly mean "wrong."
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context_budget_calculator import estimate_tokens


def extractive_summarize(text, max_sentences=2):
    """
    EXTRACTIVE SUMMARIZATION: picks out existing sentences from the
    original text, unmodified, rather than writing new ones. Scores each
    sentence by how many non-trivial words it shares with the rest of
    the document (a crude proxy for "central to the main point"), then
    keeps the highest-scoring sentences IN THEIR ORIGINAL ORDER.

    Guarantee: every word in the summary actually appeared in the
    source -- nothing can be fabricated, since nothing is rewritten.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    if len(sentences) <= max_sentences:
        return text.strip()

    all_words = re.findall(r'\w+', text.lower())
    word_freq = {}
    for w in all_words:
        word_freq[w] = word_freq.get(w, 0) + 1

    def sentence_score(sentence):
        words = re.findall(r'\w+', sentence.lower())
        return sum(word_freq.get(w, 0) for w in words) / max(1, len(words))

    scored = [(i, s, sentence_score(s)) for i, s in enumerate(sentences)]
    top = sorted(scored, key=lambda item: item[2], reverse=True)[:max_sentences]
    top_in_order = sorted(top, key=lambda item: item[0])
    return " ".join(s for _, s, _ in top_in_order)


def abstractive_summarize_simulated(text, key_terms):
    """
    ABSTRACTIVE-STYLE SUMMARIZATION (simulated): a real abstractive
    summarizer (an LLM) would REWRITE the text in new words, potentially
    shorter and clearer than any single extracted sentence. We don't
    call an LLM in this project, so this is a template-based stand-in:
    it builds a new, shorter sentence FROM scratch using the key terms
    found in the text -- demonstrating the SHAPE of abstractive
    summarization (new wording, not copied sentences) without claiming
    to replicate real LLM-quality rewriting.
    """
    found_terms = [term for term in key_terms if term.lower() in text.lower()]
    if not found_terms:
        return extractive_summarize(text, max_sentences=1)
    return f"This covers: {', '.join(found_terms)}."


def extract_key_points(text, max_points=3):
    """
    KEY POINT EXTRACTION: similar scoring to extractive summarization,
    but presents the results as a bullet list of short fragments rather
    than full prose sentences -- even more compact, at the cost of
    losing the connecting language between ideas.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    all_words = re.findall(r'\w+', text.lower())
    word_freq = {}
    for w in all_words:
        word_freq[w] = word_freq.get(w, 0) + 1

    def sentence_score(sentence):
        words = re.findall(r'\w+', sentence.lower())
        return sum(word_freq.get(w, 0) for w in words) / max(1, len(words))

    scored = sorted(((s, sentence_score(s)) for s in sentences), key=lambda item: item[1], reverse=True)
    points = [s.rstrip(".") for s, _ in scored[:max_points]]
    return "\n".join(f"- {p}" for p in points)


def grounding_check(summary, original_text):
    """
    A simple honesty check: what fraction of the summary's meaningful
    words actually appear in the original text? 100% for extractive
    summaries by construction. Lower for abstractive-style summaries if
    the rewriting introduces words that weren't really there -- exactly
    the kind of check that matters more once a REAL LLM is doing the
    rewriting and could genuinely drift from the source.
    """
    stopwords = {"this", "covers", "is", "a", "the", "and", "of", "to", "it"}
    summary_words = {w for w in re.findall(r'\w+', summary.lower()) if w not in stopwords}
    original_words = set(re.findall(r'\w+', original_text.lower()))
    if not summary_words:
        return 1.0
    grounded = summary_words & original_words
    return len(grounded) / len(summary_words)


SAMPLE_DOCUMENT = (
    "RAG stands for Retrieval-Augmented Generation. It retrieves relevant "
    "documents before generating an answer, instead of relying only on what "
    "a language model memorized during training. This matters because "
    "language models have a knowledge cutoff date and don't know about "
    "anything that happened after they were trained. RAG also helps with "
    "private data, since a model can be given access to documents it was "
    "never trained on. A typical RAG pipeline chunks documents, embeds the "
    "chunks, stores them in a vector database, retrieves relevant chunks "
    "for a query, ranks them, and generates a final answer."
)


def main():
    print("=== Summarization Techniques ===\n")

    original_tokens = estimate_tokens(SAMPLE_DOCUMENT)
    print(f"Original document: {original_tokens} tokens\n")
    print(f"  \"{SAMPLE_DOCUMENT}\"\n")

    print("--- 1. Extractive summarization ---")
    extractive = extractive_summarize(SAMPLE_DOCUMENT, max_sentences=2)
    extractive_tokens = estimate_tokens(extractive)
    print(f"  \"{extractive}\"")
    print(f"  Tokens: {extractive_tokens} ({extractive_tokens/original_tokens:.0%} of original)")
    print(f"  Grounding: {grounding_check(extractive, SAMPLE_DOCUMENT):.0%} (always 100% -- nothing was rewritten)\n")

    print("--- 2. Abstractive-style summarization (simulated) ---")
    key_terms = ["retrieval", "generation", "knowledge cutoff", "private data", "vector database"]
    abstractive = abstractive_summarize_simulated(SAMPLE_DOCUMENT, key_terms)
    abstractive_tokens = estimate_tokens(abstractive)
    print(f"  \"{abstractive}\"")
    print(f"  Tokens: {abstractive_tokens} ({abstractive_tokens/original_tokens:.0%} of original)")
    print(f"  Grounding: {grounding_check(abstractive, SAMPLE_DOCUMENT):.0%}\n")

    print("--- 3. Key point extraction ---")
    key_points = extract_key_points(SAMPLE_DOCUMENT, max_points=3)
    key_points_tokens = estimate_tokens(key_points)
    print(f"{key_points}")
    print(f"  Tokens: {key_points_tokens} ({key_points_tokens/original_tokens:.0%} of original)")
    print(f"  Grounding: {grounding_check(key_points, SAMPLE_DOCUMENT):.0%}\n")

    print(
        "When each helps:\n"
        "- Extractive: when you need a strict 'never invent anything'\n"
        "  guarantee -- the summary is always a subset of real sentences.\n"
        "- Abstractive: when extractive sentences are individually too long\n"
        "  or awkward out of context, and a genuinely rewritten, tighter\n"
        "  version would compress further than any extracted sentence could\n"
        "  -- but it needs a real LLM to do well, and needs its grounding\n"
        "  checked, since rewriting introduces a real risk of drift.\n"
        "- Key points: when the RELATIONSHIPS between ideas matter less than\n"
        "  having each individual fact available cheaply -- good for dense\n"
        "  reference material, bad for anything that depends on connecting\n"
        "  prose (cause/effect, step-by-step instructions)."
    )


if __name__ == "__main__":
    main()
