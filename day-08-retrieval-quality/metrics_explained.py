"""
metrics_explained.py

A deep, standalone walkthrough of each retrieval metric, one at a time,
with a worked example for each. The goal isn't just to show the formula
-- it's to show a case where two rankings look "similarly okay" at a
glance but score very differently on one metric versus another, so the
difference between metrics becomes concrete instead of abstract.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from evaluation_framework import precision_at_k, recall_at_k
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
from ranking_evaluation import ndcg_at_k, reciprocal_rank, average_precision  # Day 6


def explain_precision():
    print("--- Precision@K: 'Of what we returned, how much was relevant?' ---\n")
    print("Imagine 5 documents are relevant out of 100 total, and we return 5 results.")

    ranked_ids = [1, 2, 3, 4, 5]
    relevant_ids = {1, 3, 5}  # only 3 of our 5 results are actually relevant

    p = precision_at_k(ranked_ids, relevant_ids, k=5)
    print(f"Returned: {ranked_ids}")
    print(f"Actually relevant: {relevant_ids}")
    print(f"Precision@5 = {p:.2f}  (3 relevant out of 5 returned)\n")
    print(
        "When it matters: precision matters most when showing an irrelevant "
        "result has a real cost -- limited screen space, limited user "
        "patience, or (in RAG) limited context window space that an "
        "irrelevant chunk would waste.\n"
    )


def explain_recall():
    print("--- Recall@K: 'Of everything relevant, how much did we find?' ---\n")
    print("Same scenario: 3 relevant documents exist in total: {1, 3, 7}.")

    ranked_ids = [1, 2, 3, 4, 5]
    relevant_ids = {1, 3, 7}  # document 7 exists but wasn't retrieved at all

    r = recall_at_k(ranked_ids, relevant_ids, k=5)
    print(f"Returned: {ranked_ids}")
    print(f"Actually relevant (all of them): {relevant_ids}")
    print(f"Recall@5 = {r:.2f}  (found 2 of the 3 relevant documents; missed doc 7 entirely)\n")
    print(
        "When it matters: recall matters most when missing a relevant "
        "result is costly -- legal discovery, medical information, or any "
        "case where the answer being SOMEWHERE in your documents but never "
        "surfaced is a serious failure, not just an inconvenience.\n"
    )


def explain_precision_recall_tradeoff():
    print("--- Precision vs. Recall: they pull in opposite directions ---\n")
    relevant_ids = {1, 3, 5, 7, 9}  # 5 relevant documents exist in total

    small_k = [1, 2, 3]
    large_k = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    p_small = precision_at_k(small_k, relevant_ids, k=3)
    r_small = recall_at_k(small_k, relevant_ids, k=3)
    p_large = precision_at_k(large_k, relevant_ids, k=10)
    r_large = recall_at_k(large_k, relevant_ids, k=10)

    print(f"Returning only 3 results: precision={p_small:.2f}, recall={r_small:.2f}")
    print(f"Returning 10 results:     precision={p_large:.2f}, recall={r_large:.2f}\n")
    print(
        "Returning MORE results can only help recall (more chances to "
        "include a relevant one) but tends to hurt precision (more chances "
        "to include an irrelevant one too). This is why K matters, and why "
        "no single K is 'correct' for every use case.\n"
    )


def explain_map():
    print("--- MAP (Mean Average Precision): precision that cares about WHERE hits land ---\n")
    relevant_ids = {2, 5}

    ranking_a = [2, 5, 1, 3, 4]  # both relevant docs near the top
    ranking_b = [1, 3, 2, 4, 5]  # same 2 relevant docs, but scattered lower

    ap_a = average_precision(ranking_a, relevant_ids)
    ap_b = average_precision(ranking_b, relevant_ids)

    print(f"Ranking A: {ranking_a} -> Average Precision = {ap_a:.3f}")
    print(f"Ranking B: {ranking_b} -> Average Precision = {ap_b:.3f}\n")
    print(
        "Both rankings found the SAME 2 relevant documents -- recall@5 "
        "would score them identically. But MAP correctly recognizes that "
        "Ranking A put them near the top, which is much more useful to a "
        "user than Ranking B scattering them lower down.\n"
    )


def explain_ndcg():
    print("--- NDCG: ranking quality when relevance has DEGREES, not just yes/no ---\n")
    # Doc 2 is HIGHLY relevant (score 2), doc 5 is SOMEWHAT relevant (score 1).
    relevance_scores = {2: 2, 5: 1}

    ranking_a = [2, 5, 1]  # highly relevant doc first
    ranking_b = [5, 2, 1]  # somewhat relevant doc first instead

    ndcg_a = ndcg_at_k(ranking_a, relevance_scores, k=3)
    ndcg_b = ndcg_at_k(ranking_b, relevance_scores, k=3)

    print(f"Ranking A (best doc first):    {ranking_a} -> NDCG@3 = {ndcg_a:.3f}")
    print(f"Ranking B (2nd-best doc first): {ranking_b} -> NDCG@3 = {ndcg_b:.3f}\n")
    print(
        "Both rankings found the same 2 relevant documents in the same top "
        "2 positions -- precision and recall would score them identically. "
        "NDCG is the only one of these metrics that notices Ranking A put "
        "the MORE relevant document first, which is exactly the kind of "
        "distinction that matters once relevance isn't just binary.\n"
    )


def explain_mrr():
    print("--- MRR: how fast did we find the FIRST good answer? ---\n")
    relevant_ids = {5}

    fast_find = [5, 1, 2, 3]
    slow_find = [1, 2, 3, 5]

    rr_fast = reciprocal_rank(fast_find, relevant_ids)
    rr_slow = reciprocal_rank(slow_find, relevant_ids)

    print(f"Found immediately: {fast_find} -> Reciprocal Rank = {rr_fast:.3f}")
    print(f"Found last:        {slow_find} -> Reciprocal Rank = {rr_slow:.3f}\n")
    print(
        "When it matters: MRR is the right metric when a user only needs "
        "ONE good answer and stops looking once they find it -- like a "
        "'quick answer' box, or a RAG system that only ever uses the very "
        "top result. It doesn't care at all whether OTHER relevant "
        "documents exist further down, unlike MAP or recall.\n"
    )


def main():
    print("=== Retrieval Metrics, Explained One at a Time ===\n")
    explain_precision()
    explain_recall()
    explain_precision_recall_tradeoff()
    explain_map()
    explain_ndcg()
    explain_mrr()

    print("=" * 60)
    print(
        "\nSummary -- pick your metric based on what you actually care about:\n"
        "  Precision@K -> avoiding irrelevant results in a limited space\n"
        "  Recall@K    -> not missing anything relevant, even if buried\n"
        "  MAP         -> overall quality when MULTIPLE relevant results matter\n"
        "  NDCG        -> ranking quality when SOME results are more relevant than others\n"
        "  MRR         -> how fast a user finds their first good answer\n\n"
        "No single metric tells the whole story. A real evaluation (like "
        "evaluation_framework.py) reports several of these together, "
        "because a retriever can genuinely be good on one and weak on "
        "another."
    )


if __name__ == "__main__":
    main()
