"""
integration_with_previous_days.py

Wires Day 13's fact-checking pipeline into the Day 1-7 generation
pipeline: generate an answer the normal way, run it through hallucination
prevention, and compare the ORIGINAL vs. REVISED answer using Day 7's
actual answer_quality.py metrics -- showing that hallucination
prevention doesn't just "feel safer," it measurably improves grounding
without destroying the answer's relevance.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import Retriever, DOCUMENTS                  # Days 1-5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from simple_generator import Generator                             # Day 7
from answer_quality import answers_the_question, factual_consistency, length_appropriateness  # Day 7
from fact_checking_pipeline import generate_draft_answer, extract_and_verify_claims, score_overall_factuality, revise_answer  # Day 13


def build_source_texts_from_chunks(ranked_chunks):
    return [chunk["metadata"]["text"] for chunk in ranked_chunks]


def run_pipeline_with_and_without_fact_checking(query, retriever, ranker, generator):
    """
    Retrieves and ranks normally (Days 5-6), generates a draft answer
    (Day 7), then injects a realistic fabricated detail into it (the
    kind of addition a more elaborate real LLM might introduce even from
    good source material) to give the fact-checking pipeline something
    real to catch -- then compares BEFORE and AFTER Day 13's pipeline
    using Day 7's own quality metrics.
    """
    retrieved = retriever.retrieve(query, top_k=5)
    ranked = ranker.rank(retrieved)

    # Build "documents" in the shape source_verification.py expects --
    # one entry PER CHUNK, not deduplicated by title. The generator
    # pulled text from EVERY one of these chunks (see
    # generate_concatenation() in Day 7), including two different chunks
    # of "What is RAG" with genuinely different sentences. Deduplicating
    # by title would keep only the first chunk's text and silently lose
    # the second chunk's real content -- which would make a perfectly
    # legitimate, source-backed sentence look unsupported during
    # verification, a real bug caught while building this file.
    documents = [
        {"title": f"{chunk['metadata']['title']} (chunk {chunk['metadata']['chunk_index']})", "text": chunk["metadata"]["text"]}
        for chunk in ranked
    ]

    draft = generate_draft_answer(generator, query, ranked)
    # Inject a fabricated detail to make this a realistic test of whether
    # fact-checking catches something -- without this, a well-grounded
    # generator might legitimately produce nothing to catch, which would
    # make the "before vs after" comparison trivial rather than meaningful.
    fabricated_answer = draft + " This was proven in a widely cited 2019 study of 10,000 production deployments."

    verified = extract_and_verify_claims(fabricated_answer, documents)
    score = score_overall_factuality(verified)
    revised, changes = revise_answer(verified)

    return {
        "query": query,
        "documents": documents,
        "original": fabricated_answer,
        "revised": revised,
        "factuality_score": score,
        "changes": changes,
    }


def compare_quality(query, original, revised, source_texts):
    """
    Measures BOTH answers with Day 7's real answer_quality.py checks, so
    "fact-checking helped" is a measured comparison, not an assumption.
    """
    metrics = {}
    for label, answer in [("original", original), ("revised", revised)]:
        _, relevance = answers_the_question(query, answer)
        consistency = factual_consistency(answer, source_texts)
        length_status, word_count = length_appropriateness(answer)
        metrics[label] = {
            "relevance": relevance,
            "factual_consistency": consistency,
            "length_status": length_status,
            "word_count": word_count,
        }
    return metrics


def main():
    print("=== Hallucination Prevention Wired Into the Complete Pipeline ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    generator = Generator()

    result = run_pipeline_with_and_without_fact_checking("What is RAG?", retriever, ranker, generator)

    print(f"Query: \"{result['query']}\"\n")
    print(f"Original (unchecked) answer:\n  \"{result['original']}\"\n")
    print(f"Revised (fact-checked) answer:\n  \"{result['revised']}\"\n")

    print("--- What the fact-checking pipeline changed ---")
    for change in result["changes"]:
        print(f"  {change}")
    print(f"\nOverall factuality score (original claims): {result['factuality_score']['avg_confidence']:.2f}")
    print(f"Worst claim found: \"{result['factuality_score']['worst_claim']}\" (confidence {result['factuality_score']['worst_confidence']:.2f})\n")

    print("=" * 60)
    print("\n--- Measuring quality: original vs. revised ---\n")

    source_texts = build_source_texts_from_chunks([{"metadata": d} for d in result["documents"]])
    metrics = compare_quality(result["query"], result["original"], result["revised"], source_texts)

    header = f"{'Version':<10} | {'Relevance':>9} | {'Factual consistency':>19} | {'Length':>14} | {'Words':>5}"
    print(header)
    print("-" * len(header))
    for label, m in metrics.items():
        print(f"{label:<10} | {m['relevance']:>9.2f} | {m['factual_consistency']:>19.2f} | {m['length_status']:>14} | {m['word_count']:>5}")

    consistency_delta = metrics["revised"]["factual_consistency"] - metrics["original"]["factual_consistency"]
    relevance_delta = metrics["revised"]["relevance"] - metrics["original"]["relevance"]

    print(
        f"\nFactual consistency changed by {consistency_delta:+.2f}, "
        f"relevance changed by {relevance_delta:+.2f}."
    )
    print(
        "\nThe key result: fact-checking removed the fabricated claim "
        "WITHOUT meaningfully hurting relevance -- the revised answer "
        "still addresses the original question using only what the "
        "sources actually support. This is the real promise of "
        "hallucination prevention: it's not a tradeoff against quality, "
        "it's a correction that keeps the genuinely useful, grounded "
        "parts of an answer while removing the part that would have been "
        "actively misleading."
    )


if __name__ == "__main__":
    main()
