"""
metric_analysis.py

A single average NDCG score tells you almost nothing about WHY it's
that number. This file breaks results down by query type and
difficulty, looks for patterns in what's failing, and turns that into
an actionable next step -- not just "the score is 0.85."
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import evaluate_retriever


def group_by(per_query_results, key):
    groups = {}
    for r in per_query_results:
        groups.setdefault(r[key], []).append(r)
    return groups


def average(values):
    return sum(values) / len(values) if values else 0.0


def breakdown_by_category(per_query_results, category_key, metric_key="ndcg"):
    """
    BREAK DOWN PERFORMANCE BY QUERY TYPE/DIFFICULTY: averages one metric
    within each category, so you can see "easy queries score 0.95, hard
    queries score 0.55" instead of one blended 0.80 that hides both
    facts equally.
    """
    groups = group_by(per_query_results, category_key)
    return {category: average([r[metric_key] for r in results]) for category, results in groups.items()}


def find_worst_queries(per_query_results, metric_key="ndcg", n=3):
    """
    WHERE RETRIEVAL FAILS: sorts queries by score, ascending, so the
    worst performers surface first. These are the specific, concrete
    cases worth digging into with per_query_diagnosis.py -- much more
    useful than staring at an aggregate number.
    """
    return sorted(per_query_results, key=lambda r: r[metric_key])[:n]


def identify_patterns(per_query_results, metric_key="ndcg", threshold=0.7):
    """
    IDENTIFY PATTERNS IN FAILURES: checks whether failing queries
    cluster around a specific difficulty or query type. If every failing
    query is "hard" difficulty, that's a very different problem (the
    hard cases are genuinely hard) than if failures are scattered evenly
    across easy and hard alike (something is broken more generally).
    """
    failing = [r for r in per_query_results if r[metric_key] < threshold]
    if not failing:
        return "No queries fell below the threshold -- no failure pattern to report."

    failing_difficulties = [r["difficulty"] for r in failing]
    failing_types = [r["query_type"] for r in failing]

    difficulty_counts = {d: failing_difficulties.count(d) for d in set(failing_difficulties)}
    type_counts = {t: failing_types.count(t) for t in set(failing_types)}

    lines = [f"{len(failing)} of {len(per_query_results)} queries scored below {threshold}:"]
    lines.append(f"  By difficulty: {difficulty_counts}")
    lines.append(f"  By query type: {type_counts}")

    if len(difficulty_counts) == 1:
        only_difficulty = list(difficulty_counts)[0]
        lines.append(
            f"  Pattern: ALL failures are '{only_difficulty}' difficulty -- "
            f"this suggests the retriever handles typical cases fine, but "
            f"struggles specifically with queries in that difficulty band."
        )
    return "\n".join(lines)


def suggest_root_causes(failing_queries):
    """
    ROOT CAUSE ANALYSIS: a simple rule-based first pass at WHY a query
    might be failing, based on characteristics of the query itself. This
    isn't a diagnosis -- it's a set of hypotheses worth checking, which
    per_query_diagnosis.py then investigates properly for a specific
    case.
    """
    suggestions = []
    for r in failing_queries:
        query = r["query"]
        hypotheses = []

        if len(query.split()) > 10:
            hypotheses.append("long, multi-part query -- may need query decomposition")
        if "?" not in query:
            hypotheses.append("not phrased as a question -- may confuse question-oriented matching")
        if r["query_type"] == "comparison":
            hypotheses.append("comparison query -- may need multiple documents, not just one best match")
        if r["precision"] > 0 and r["recall"] < 0.5:
            hypotheses.append("found SOME relevant info but missed other relevant docs -- possible recall gap")

        if not hypotheses:
            hypotheses.append("no obvious pattern from query text alone -- needs manual inspection")

        suggestions.append((query, hypotheses))
    return suggestions


def main():
    print("=== Metric Analysis: Finding What's Actually Breaking ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)

    dataset = build_manual_ground_truth_dataset()
    results = evaluate_retriever(retrieve_fn, dataset, k=3)
    per_query = results["per_query_results"]

    print(f"Overall NDCG@3: {results['avg_ndcg']:.3f}\n")

    print("--- Breakdown by difficulty ---")
    by_difficulty = breakdown_by_category(per_query, "difficulty")
    for difficulty, score in sorted(by_difficulty.items(), key=lambda pair: pair[1]):
        print(f"  {difficulty:8s}: {score:.3f}")
    print()

    print("--- Breakdown by query type ---")
    by_type = breakdown_by_category(per_query, "query_type")
    for query_type, score in sorted(by_type.items(), key=lambda pair: pair[1]):
        print(f"  {query_type:12s}: {score:.3f}")
    print()

    print("--- Worst-performing queries ---")
    worst = find_worst_queries(per_query, n=2)
    for r in worst:
        print(f"  NDCG={r['ndcg']:.2f}  [{r['difficulty']}] \"{r['query']}\"")
    print()

    print("--- Failure pattern analysis ---")
    print(identify_patterns(per_query, threshold=0.7))
    print()

    print("--- Suggested root causes for underperforming queries ---")
    failing = [r for r in per_query if r["ndcg"] < 0.7]
    for query, hypotheses in suggest_root_causes(failing):
        print(f"  \"{query}\"")
        for h in hypotheses:
            print(f"    - {h}")

    worst_difficulty = min(by_difficulty, key=by_difficulty.get)
    worst_type = min(by_type, key=by_type.get)
    print(
        f"\nWhat makes this actionable: knowing the overall NDCG is "
        f"{results['avg_ndcg']:.3f} tells you almost nothing to DO. Knowing "
        f"that '{worst_difficulty}' difficulty queries specifically "
        f"underperform (and that both of this dataset's medium-difficulty "
        f"queries are phrased conceptually, not matching a document title "
        f"directly) points toward a concrete next step: improve how "
        f"differently-phrased queries get matched to source text (better "
        f"embeddings, or query expansion like Day 5's query_preprocessing.py) "
        f"-- rather than a vague 'try to make retrieval better' with no "
        f"specific target."
    )


if __name__ == "__main__":
    main()
