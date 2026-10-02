"""
cost_analysis_at_scale.py

Builds on Day 9's cost math, but tracks it across GROWING scale
specifically: embedding costs, storage costs, and compute costs as a
document set grows from 1,000 to 10 million. Shows where each cost
category actually starts to dominate the budget.
"""


def embedding_cost(num_documents, avg_tokens_per_doc=200, price_per_1k_tokens=0.00002):
    """One-time cost to embed the full document set."""
    return (num_documents * avg_tokens_per_doc / 1000) * price_per_1k_tokens


def storage_cost_per_month(num_documents, embedding_dimensions=1536, bytes_per_float=4, price_per_gb_month=0.023):
    """
    Monthly storage cost for keeping all the embeddings around (a rough
    stand-in for real vector database or object storage pricing, like
    cloud block storage pricing).
    """
    bytes_per_embedding = embedding_dimensions * bytes_per_float
    total_bytes = num_documents * bytes_per_embedding
    total_gb = total_bytes / (1024 ** 3)
    return total_gb * price_per_gb_month


def compute_cost_per_month(num_documents, queries_per_month, price_per_query_ms=0.000001, latency_ms_per_1k_docs=2.0):
    """
    Monthly compute cost for SEARCHING the index, which (for brute force)
    scales with both query volume AND document count -- more documents
    means each individual search takes longer, and more queries means
    more searches happen. This is a simplified cost model, but the
    SHAPE (cost grows with both factors multiplied together) matches
    reality for an unindexed brute-force search.
    """
    latency_ms_per_query = (num_documents / 1000) * latency_ms_per_1k_docs
    total_compute_ms = latency_ms_per_query * queries_per_month
    return total_compute_ms * price_per_query_ms


def total_cost_breakdown(num_documents, queries_per_month=100_000):
    embed = embedding_cost(num_documents)
    storage = storage_cost_per_month(num_documents)
    compute = compute_cost_per_month(num_documents, queries_per_month)
    return embed, storage, compute


def main():
    print("=== Cost Analysis at Scale ===\n")

    sizes = [1_000, 10_000, 100_000, 1_000_000, 10_000_000]
    queries_per_month = 100_000

    header = f"{'Documents':>12} | {'Embed (one-time)':>17} | {'Storage/mo':>11} | {'Compute/mo':>11} | {'Total year 1':>13}"
    print(header)
    print("-" * len(header))

    results = []
    for size in sizes:
        embed, storage, compute = total_cost_breakdown(size, queries_per_month)
        year_1_total = embed + (storage + compute) * 12
        results.append({"size": size, "embed": embed, "storage": storage, "compute": compute, "year_1": year_1_total})
        print(f"{size:>12,} | ${embed:>16.2f} | ${storage:>10.4f} | ${compute:>10.2f} | ${year_1_total:>12.2f}")

    print()
    print("--- Which cost category dominates, by scale ---\n")
    for r in results:
        costs = {"embedding (one-time)": r["embed"], "storage (monthly)": r["storage"] * 12, "compute (monthly)": r["compute"] * 12}
        dominant = max(costs, key=costs.get)
        print(f"  {r['size']:>10,} documents: dominant year-1 cost is {dominant} (${costs[dominant]:.2f}/year)")
    print(
        "\n(Compute dominates at EVERY scale in this cost model, not just "
        "at the high end -- a useful finding in itself: with brute-force "
        "search and this query volume, compute was never the cost to "
        "ignore, even at a modest 1,000 documents. Your own workload's "
        "balance will differ based on query volume and document size, "
        "which is exactly why it's worth running this calculation on your "
        "real numbers instead of assuming a fixed ranking of cost "
        "categories.)"
    )

    print(
        "\nNotice compute cost grows the FASTEST as document count grows -- "
        "it scales with document count AND query volume multiplied "
        "together, which is exactly the brute-force-search cost problem "
        "indexing_impact.py addressed. This is a concrete financial reason "
        "indexing matters at scale, not just a latency one: at 10 million "
        "documents with brute-force search, compute cost alone could "
        "dwarf storage and embedding costs combined.\n\n"
        "--- Cost optimization strategies, ranked by typical impact ---\n"
        "  1. Index instead of brute force -- directly cuts the fastest-\n"
        "     growing cost category (compute), often by orders of magnitude.\n"
        "  2. Cache aggressively (Day 10's caching_strategies.py) -- avoids\n"
        "     paying for repeated work entirely.\n"
        "  3. Right-size your embedding model (Day 9) -- a smaller model\n"
        "     that's still good enough cuts embedding cost and dimension\n"
        "     count (which also cuts storage).\n"
        "  4. Quantize stored embeddings (Day 9) -- directly reduces\n"
        "     storage cost, with a measured quality tradeoff.\n\n"
        "Budgeting takeaway: embedding cost is a one-time, predictable "
        "expense. Storage and compute are RECURRING and grow with usage -- "
        "budget for them as ongoing operational cost, not a one-time setup "
        "line item, and revisit the estimate as both document count and "
        "query volume grow over time."
    )


if __name__ == "__main__":
    main()
