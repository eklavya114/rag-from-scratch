"""
quality_vs_cost.py

Reuses model_comparison.py's three simulated models and measured NDCG
scores, and turns the quality difference into real cost math: what does
each model actually cost to run at a given workload, and is the quality
gain worth the extra spend?
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
from model_comparison import MODELS, ModelComparator
from basic_retriever import DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset


# Real-world reference prices (per 1,000 tokens), approximating actual
# published embedding API pricing as of this writing -- used to make the
# cost math concrete, not to simulate retrieval quality (that's still
# done with the fake vocabularies in model_comparison.py).
REAL_WORLD_PRICING = {
    "small/fast tier (e.g. text-embedding-3-small)": 0.00002,
    "large/high-quality tier (e.g. text-embedding-3-large)": 0.00013,
    "local/self-hosted (compute cost only, rough estimate)": 0.000005,
}


def estimate_tokens(text):
    """A simple word-count-based token estimate (see token_counting.py-style logic in Day 11 if it exists)."""
    return int(len(text.split()) * 1.3)  # rough rule of thumb: ~1.3 tokens per word


def calculate_workload_cost(num_documents, avg_tokens_per_doc, num_queries_per_month, price_per_1k_tokens):
    """
    TOTAL COST OF OWNERSHIP: embedding cost isn't just "per query" -- it's
    the one-time cost of embedding your document set PLUS the recurring
    cost of embedding every incoming query. Both matter, but at
    different frequencies.
    """
    one_time_indexing_cost = (num_documents * avg_tokens_per_doc / 1000) * price_per_1k_tokens
    monthly_query_cost = (num_queries_per_month * 15 / 1000) * price_per_1k_tokens  # assume ~15 tokens/query
    return one_time_indexing_cost, monthly_query_cost


def show_tradeoff_curve(results):
    """
    Plots a simple text-based quality-vs-cost curve using the REAL
    measured NDCG scores from model_comparison.py -- not made-up numbers
    -- so the "tradeoff" being shown is grounded in an actual evaluation.
    """
    print("--- Quality vs. cost tradeoff (measured) ---\n")
    max_cost = max(r["model"].cost_per_1k_tokens for r in results.values()) or 1
    for name, r in results.items():
        cost = r["model"].cost_per_1k_tokens
        ndcg = r["avg_ndcg"]
        cost_bar = "$" * (int((cost / max_cost) * 15) if max_cost else 0)
        quality_bar = "#" * int(ndcg * 20)
        print(f"  {name:<32}")
        print(f"    Cost:    {cost_bar:<15} (${cost:.3f}/1K tokens)")
        print(f"    Quality: {quality_bar:<20} (NDCG {ndcg:.3f})")
    print()


def recommend_for_budget(results, monthly_budget):
    """
    A simple recommendation: among models whose estimated FIRST-MONTH
    cost fits the budget, pick the one with the best measured quality.

    First-month cost = one-time indexing cost + that month's query cost.
    Using only the recurring monthly query cost would be misleading for
    a new deployment -- the one-time indexing bill still has to be paid
    before any queries can even run.
    """
    affordable = []
    for name, r in results.items():
        one_time_cost, monthly_cost = calculate_workload_cost(
            num_documents=1000, avg_tokens_per_doc=200, num_queries_per_month=10000,
            price_per_1k_tokens=r["model"].cost_per_1k_tokens,
        )
        first_month_total = one_time_cost + monthly_cost
        if first_month_total <= monthly_budget:
            affordable.append((name, r["avg_ndcg"], first_month_total))

    if not affordable:
        return None
    return max(affordable, key=lambda item: item[1])


def main():
    print("=== Quality vs. Cost Analysis ===\n")

    dataset = build_manual_ground_truth_dataset()
    comparator = ModelComparator(DOCUMENTS, dataset)
    results = comparator.compare(MODELS, k=3)

    show_tradeoff_curve(results)

    print("--- Total cost of ownership example ---\n")
    print("Workload: 1,000 documents (avg 200 tokens each), 10,000 queries/month\n")
    for name, r in results.items():
        price = r["model"].cost_per_1k_tokens
        one_time, monthly = calculate_workload_cost(1000, 200, 10000, price)
        print(f"  {name:<32}: one-time indexing ${one_time:.2f}, then ${monthly:.2f}/month for queries")
    print()

    print("--- Real-world reference pricing (approximate) ---\n")
    for tier, price in REAL_WORLD_PRICING.items():
        one_time, monthly = calculate_workload_cost(1000, 200, 10000, price)
        print(f"  {tier}")
        print(f"    ${price:.6f}/1K tokens -> one-time ${one_time:.2f}, then ${monthly:.2f}/month")
    print()

    print("--- Recommendation by first-month budget (indexing + queries) ---\n")
    for budget in [0.01, 10.00, 50.00]:
        best = recommend_for_budget(results, budget)
        if best:
            name, ndcg, cost = best
            print(f"  Budget ${budget:>6.2f} -> best affordable: {name} (NDCG {ndcg:.3f}, first month ${cost:.4f})")
        else:
            print(f"  Budget ${budget:>6.2f} -> nothing fits, even the cheapest option")

    print(
        "\nThe real takeaway isn't 'always pick the cheapest' or 'always "
        "pick the best' -- it's that the quality gain needs to be worth "
        "the cost gain for YOUR workload. Going from the medium to the "
        "high-quality model here cost roughly 6.5x more per token but only "
        "improved NDCG by about 8% (0.878 -> 0.952). Whether that's worth "
        "it depends entirely on how much retrieval quality actually "
        "matters for your product -- a customer-facing legal assistant "
        "might gladly pay it; a low-stakes internal FAQ bot probably "
        "shouldn't."
    )


if __name__ == "__main__":
    main()
