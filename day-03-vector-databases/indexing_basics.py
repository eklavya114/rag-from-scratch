"""
indexing_basics.py

Shows WHY real vector databases use indexing instead of brute force,
with actual timing numbers, not just claims.

We build two search methods over the same random dataset:
  1. brute_force_search() -- checks every vector. Always exactly correct.
  2. simple_graph_search() -- a simplified, HNSW-inspired approach. Builds
     a small "neighbor graph" ahead of time, then searches by hopping
     between neighbors instead of checking everything.

Then we time both at a few different dataset sizes and see how the gap
grows. This is a TOY version of HNSW meant to show the core idea (skip
most of the data by following neighbor connections) -- real HNSW
implementations are more sophisticated, but the underlying trade-off
(a little accuracy for a lot of speed) is the same.
"""

import math
import random
import time


def cosine_similarity(vector_a, vector_b):
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    mag_a = math.sqrt(sum(a * a for a in vector_a))
    mag_b = math.sqrt(sum(b * b for b in vector_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def make_random_vectors(count, dimensions=8, seed=42):
    """
    Generates `count` random vectors with `dimensions` numbers each.
    Used to simulate a dataset of embeddings at various sizes, so we can
    benchmark search speed without needing real documents.
    """
    rng = random.Random(seed)
    return [[rng.random() for _ in range(dimensions)] for _ in range(count)]


def brute_force_search(query, vectors, top_k=5):
    """
    Checks the query against every single vector. Always finds the true
    best matches, but the amount of work grows directly with the number
    of vectors -- 10x the data means roughly 10x the time.
    """
    scored = [(i, cosine_similarity(query, v)) for i, v in enumerate(vectors)]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]


class SimpleGraphIndex:
    """
    A simplified, HNSW-inspired index. This is NOT real HNSW -- real HNSW
    uses multiple layers and careful graph-building rules. This is a
    toy version that captures the core idea: build neighbor connections
    once, then search by hopping toward better matches instead of
    checking every vector.
    """

    def __init__(self, vectors, num_neighbors=20, seed=42):
        self.vectors = vectors
        self.num_neighbors = num_neighbors
        self.graph = self._build_graph(seed)

    def _build_graph(self, seed):
        """
        For each vector, connect it to a handful of OTHER vectors that
        are actually close to it (its "neighbors"). This is the one-time
        setup cost that makes searching faster later -- real vector
        databases pay this cost once, when data is added, not on every
        search.
        """
        rng = random.Random(seed)
        graph = {}

        for i, vector in enumerate(self.vectors):
            # To keep graph-building itself fast, we only compare against
            # a random sample of candidates rather than everyone -- a
            # simplification real HNSW avoids with smarter construction,
            # but it's good enough to demonstrate the search speedup.
            # The sample needs to be reasonably large relative to
            # num_neighbors, or most sampled candidates end up being
            # picked as "neighbors" almost at random, making the graph
            # a poor map of what's actually nearby.
            sample_size = min(150, len(self.vectors))
            candidates = rng.sample(range(len(self.vectors)), sample_size)

            scored = [
                (j, cosine_similarity(vector, self.vectors[j]))
                for j in candidates if j != i
            ]
            scored.sort(key=lambda pair: pair[1], reverse=True)

            graph[i] = [j for j, _ in scored[:self.num_neighbors]]

        return graph

    def search(self, query, top_k=5, entry_points=None, max_steps=40, beam_width=None):
        """
        A simplified "beam search" over the neighbor graph: start from a
        handful of random entry points, and at each step keep the best
        `beam_width` candidates found so far, expanding their neighbors
        and folding those in too. This is closer to how real HNSW search
        works than a single greedy walk -- a pure greedy walk gets stuck
        the moment it hits one local peak, even if a better one is one
        more hop away through a different neighbor. Keeping a small beam
        of candidates makes the search far more likely to actually reach
        the good part of the graph, while still only touching a small
        fraction of the total vectors.
        """
        # Scale search effort with dataset size, the same way real vector
        # databases let you tune a parameter like "ef_search" higher for
        # bigger collections. A fixed, small beam that works fine on 1,000
        # vectors explores too small a slice of a 100,000-vector graph to
        # reliably find the true best matches -- this keeps the search
        # honestly accurate as the dataset grows, not just fast.
        if entry_points is None:
            entry_points = max(10, len(self.vectors) // 500)
        if beam_width is None:
            beam_width = max(10, len(self.vectors) // 500)

        rng = random.Random()
        visited = set()
        scored = {}  # index -> similarity, for everything we've looked at

        entry_ids = rng.sample(range(len(self.vectors)), min(entry_points, len(self.vectors)))
        frontier = list(entry_ids)

        for _ in range(max_steps):
            if not frontier:
                break

            # Score every candidate in the current frontier.
            for idx in frontier:
                if idx not in visited:
                    visited.add(idx)
                    scored[idx] = cosine_similarity(query, self.vectors[idx])

            # Keep only the best `beam_width` candidates seen so far --
            # this is the "beam" -- and expand outward from just those,
            # instead of from every vector we've ever touched.
            beam = sorted(scored.items(), key=lambda pair: pair[1], reverse=True)[:beam_width]

            next_frontier = []
            for idx, _ in beam:
                for neighbor in self.graph[idx]:
                    if neighbor not in visited:
                        next_frontier.append(neighbor)

            if not next_frontier:
                break
            frontier = next_frontier

        ranked = sorted(scored.items(), key=lambda pair: pair[1], reverse=True)
        return ranked[:top_k], len(visited)


def benchmark(size):
    """
    Times brute force vs the graph index on a dataset of the given size,
    and reports how many vectors each method actually had to check.
    """
    vectors = make_random_vectors(size, seed=42)
    # Use a different seed for the query than the dataset. Both default to
    # the same seed otherwise, which makes the query start from the same
    # random sequence as the dataset and land suspiciously close to (or
    # exactly on) one of the stored vectors -- skewing the benchmark.
    query = make_random_vectors(1, seed=999)[0]

    # Time brute force.
    start = time.perf_counter()
    brute_results = brute_force_search(query, vectors, top_k=5)
    brute_time = time.perf_counter() - start

    # Time index building + search separately, since building happens
    # once but search happens over and over -- that's the whole point.
    build_start = time.perf_counter()
    index = SimpleGraphIndex(vectors)
    build_time = time.perf_counter() - build_start

    search_start = time.perf_counter()
    graph_results, visited_count = index.search(query, top_k=5)
    graph_search_time = time.perf_counter() - search_start

    brute_top_id, brute_top_score = brute_results[0]
    graph_top_id, graph_top_score = graph_results[0]
    found_exact_same_match = brute_top_id == graph_top_id
    # Even when it's not the EXACT same vector, an approximate index is
    # doing its job if the similarity score it found is nearly as good
    # as the true best -- that's the accuracy/speed trade-off in action.
    score_gap = brute_top_score - graph_top_score

    print(f"Dataset size: {size:,} vectors")
    print(f"  Brute force search time:     {brute_time * 1000:8.3f} ms  (checked all {size:,} vectors)")
    print(f"  Graph index build time:      {build_time * 1000:8.3f} ms  (one-time cost)")
    print(f"  Graph index search time:     {graph_search_time * 1000:8.3f} ms  (checked only {visited_count:,} vectors)")
    print(f"  Brute force top score:       {brute_top_score:.4f}")
    print(f"  Graph index top score:       {graph_top_score:.4f}  (gap: {score_gap:.4f})")
    print(f"  Found the exact same match?  {found_exact_same_match}")
    print()


def main():
    print("=== Indexing Basics: Brute Force vs. Graph Index ===\n")

    for size in [1_000, 10_000, 100_000]:
        benchmark(size)

    print(
        "What to notice: brute force search time grows directly with dataset "
        "size, because it checks every vector, every time. The graph index "
        "pays a one-time cost to build neighbor connections, but then each "
        "search only checks a small fraction of the data -- and search time "
        "barely grows as the dataset gets bigger. That's the whole point of "
        "indexing: pay once, search fast forever after."
    )


if __name__ == "__main__":
    main()
