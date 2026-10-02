"""
sharding_and_distribution.py

Sharding splits your data across multiple "servers" so no single one has
to hold everything. We simulate several independent in-memory "shards"
(each a small vector index) and route documents and queries to the right
one, showing both the performance benefit and the real complexity it
adds.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
from indexing_basics import make_random_vectors, brute_force_search, cosine_similarity  # Day 3


class Shard:
    """One independent partition of the overall index -- in a real system, this would be a separate server/process."""

    def __init__(self, shard_id):
        self.shard_id = shard_id
        self.vectors = []

    def add(self, vector):
        self.vectors.append(vector)

    def search(self, query, top_k):
        return brute_force_search(query, self.vectors, top_k=top_k)


def document_sharding(vectors, num_shards):
    """
    DOCUMENT SHARDING: splits a document set across N shards, round-
    robin, so each shard holds roughly 1/N of the total. At query time,
    EVERY shard still has to be searched (the query doesn't know in
    advance which shard holds the best match) -- the win is that each
    shard search happens on a much smaller slice of data, and shards can
    be searched IN PARALLEL across different machines/processes.
    """
    shards = [Shard(i) for i in range(num_shards)]
    for i, vector in enumerate(vectors):
        shards[i % num_shards].add(vector)
    return shards


def scatter_gather_search(shards, query, top_k):
    """
    SCATTER-GATHER: the standard pattern for querying a sharded index --
    "scatter" the query to every shard, then "gather" the results and
    merge them into one final ranked list. This is what document
    sharding requires, since relevant results could be on any shard.
    """
    all_results = []
    for shard in shards:
        shard_results = shard.search(query, top_k=top_k)
        for idx, score in shard_results:
            all_results.append((shard.shard_id, idx, score))

    all_results.sort(key=lambda r: r[2], reverse=True)
    return all_results[:top_k]


class QueryRouter:
    """
    QUERY SHARDING (a different strategy from document sharding): routes
    each query to exactly ONE shard based on some property of the query
    itself -- here, which "topic" it belongs to. This only works when
    you can reliably predict which shard holds the relevant data for a
    given query; it avoids scatter-gather's "ask every shard" cost
    entirely, at the price of needing that routing logic to be correct.
    """

    def __init__(self, shards_by_topic):
        self.shards_by_topic = shards_by_topic

    def route(self, query_topic):
        return self.shards_by_topic.get(query_topic)


def measure_sharded_vs_single(total_size, num_shards):
    """
    Compares a single unsharded index against the same data split across
    shards, searched one at a time (simulating sequential scatter-gather
    -- a real system would parallelize this across machines, which
    query_optimization.py and batching_and_parallelization.py already
    showed the benefit of).
    """
    vectors = make_random_vectors(total_size, dimensions=8, seed=42)
    query = make_random_vectors(1, dimensions=8, seed=999)[0]

    start = time.perf_counter()
    brute_force_search(query, vectors, top_k=5)
    single_time = time.perf_counter() - start

    shards = document_sharding(vectors, num_shards)
    start = time.perf_counter()
    scatter_gather_search(shards, query, top_k=5)
    sharded_time = time.perf_counter() - start

    return single_time, sharded_time


def main():
    print("=== Sharding and Distribution ===\n")

    print("--- What is sharding? ---\n")
    print(
        "Sharding splits a large dataset across multiple independent "
        "partitions (\"shards\"), each potentially living on a different "
        "server. No single machine needs to hold the entire dataset in "
        "memory, and work can happen in parallel across shards.\n"
    )

    print("--- Document sharding + scatter-gather ---\n")
    total_size = 10_000
    num_shards = 4
    single_time, sharded_time = measure_sharded_vs_single(total_size, num_shards)
    print(f"Searching {total_size:,} vectors as one index:         {single_time*1000:.2f} ms")
    print(f"Searching the same data split into {num_shards} shards (sequential scatter-gather): {sharded_time*1000:.2f} ms")
    print(
        "\n(Sequentially searching each shard one at a time, as done here, "
        "doesn't save time by itself -- the real win comes from searching "
        "shards IN PARALLEL across separate machines, which turns the "
        "total shard search time from 'sum of all shards' into roughly "
        "'the slowest single shard.' Day 10's batching_and_parallelization.py "
        "demonstrates exactly that kind of parallel speedup.)\n"
    )

    print("--- Query sharding (route, don't scatter) ---\n")
    shards_by_topic = {"legal": Shard("legal"), "medical": Shard("medical"), "code": Shard("code")}
    router = QueryRouter(shards_by_topic)
    for topic in ["legal", "medical", "unknown_topic"]:
        target_shard = router.route(topic)
        if target_shard:
            print(f"  Query topic '{topic}' -> routed directly to shard '{target_shard.shard_id}' (only 1 shard searched)")
        else:
            print(f"  Query topic '{topic}' -> no matching shard found; would need a fallback (e.g. scatter-gather all shards)")

    print(
        "\n--- The complexity cost of sharding ---\n"
        "Sharding isn't free:\n"
        "  - Document sharding needs scatter-gather logic, and merging\n"
        "    results from multiple shards correctly (including handling a\n"
        "    shard that's slow or down).\n"
        "  - Query sharding needs reliable routing logic -- get it wrong and\n"
        "    queries silently miss the shard that actually had the answer.\n"
        "  - Rebalancing shards as data grows unevenly is its own ongoing\n"
        "    operational problem.\n"
        "  - Debugging gets harder: a problem could be in the routing, one\n"
        "    specific shard, or how results get merged.\n\n"
        "Sharding is what makes TRUE scale (far beyond what one machine's "
        "memory can hold) possible -- but it should be reached for once "
        "you've actually hit that wall, not as a default starting "
        "architecture for a system that fits comfortably on one machine."
    )


if __name__ == "__main__":
    main()
