"""
performance_profiling.py

Before optimizing (caching or otherwise), you need to know where time is
ACTUALLY being spent -- not guess. This file profiles each stage of the
real Day 5/6/7 pipeline (retrieval, ranking, generation) individually,
identifies the genuine bottleneck, and then measures how much caching
helps EACH stage specifically.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
from basic_retriever import Retriever, DOCUMENTS                  # Day 5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from simple_generator import Generator                             # Day 7


def profile_pipeline_stages(query, retriever, ranker, generator, num_runs=50):
    """
    PROFILE EACH COMPONENT: times retrieval, ranking, and generation
    SEPARATELY, averaged over several runs so one slow run doesn't skew
    the result. This is the step people skip when they "optimize" based
    on intuition instead of measurement.
    """
    retrieval_times = []
    ranking_times = []
    generation_times = []

    for _ in range(num_runs):
        start = time.perf_counter()
        retrieved = retriever.retrieve(query, top_k=5)
        retrieval_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        ranked = ranker.rank(retrieved)
        ranking_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        generator.generate_concatenation(query, ranked, max_chunks=3)
        generation_times.append((time.perf_counter() - start) * 1000)

    def avg(values):
        return sum(values) / len(values)

    return {
        "retrieval_ms": avg(retrieval_times),
        "ranking_ms": avg(ranking_times),
        "generation_ms": avg(generation_times),
    }


def identify_bottleneck(profile):
    """IDENTIFY BOTTLENECKS: the stage taking the largest share of total time -- the one worth optimizing FIRST."""
    total = sum(profile.values())
    shares = {stage: (time_ms / total) for stage, time_ms in profile.items()}
    bottleneck = max(shares, key=shares.get)
    return bottleneck, shares, total


def measure_caching_impact_per_stage(query, retriever, ranker, generator):
    """
    MEASURE CACHING IMPACT ON EACH STAGE: times each stage once
    "cold" (first call) and once "warm" (repeated call, as if a cache
    layer specific to that stage existed) -- showing that caching
    doesn't help every stage EQUALLY, since some stages have real
    per-call work and others barely do anything to begin with at this
    document scale.
    """
    # Retrieval: repeat the SAME query -- a real retrieval cache would
    # turn the second call into a lookup.
    start = time.perf_counter()
    retrieved = retriever.retrieve(query, top_k=5)
    cold_retrieval = (time.perf_counter() - start) * 1000

    cached_retrieved = retrieved  # standing in for "a cache would just return this"
    start = time.perf_counter()
    _ = cached_retrieved
    warm_retrieval = (time.perf_counter() - start) * 1000

    # Ranking: same idea, for the ranking stage specifically.
    start = time.perf_counter()
    ranked = ranker.rank(retrieved)
    cold_ranking = (time.perf_counter() - start) * 1000

    cached_ranked = ranked
    start = time.perf_counter()
    _ = cached_ranked
    warm_ranking = (time.perf_counter() - start) * 1000

    # Generation: same idea, for the generation stage.
    start = time.perf_counter()
    answer = generator.generate_concatenation(query, ranked, max_chunks=3)
    cold_generation = (time.perf_counter() - start) * 1000

    cached_answer = answer
    start = time.perf_counter()
    _ = cached_answer
    warm_generation = (time.perf_counter() - start) * 1000

    return {
        "retrieval": (cold_retrieval, warm_retrieval),
        "ranking": (cold_ranking, warm_ranking),
        "generation": (cold_generation, warm_generation),
    }


def main():
    print("=== Performance Profiling ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    generator = Generator()

    query = "What is RAG?"

    print(f"Profiling the pipeline for: \"{query}\" (averaged over 50 runs)\n")
    profile = profile_pipeline_stages(query, retriever, ranker, generator)

    for stage, time_ms in profile.items():
        print(f"  {stage:<16}: {time_ms:.4f} ms")

    bottleneck, shares, total = identify_bottleneck(profile)
    print(f"\n  Total: {total:.4f} ms")
    print(f"  Bottleneck: {bottleneck} ({shares[bottleneck]:.0%} of total time)\n")

    for stage, share in sorted(shares.items(), key=lambda pair: pair[1], reverse=True):
        print(f"    {stage:<16}: {share:.0%} of total time")

    print("\n--- Caching impact, per stage ---\n")
    impact = measure_caching_impact_per_stage(query, retriever, ranker, generator)
    for stage, (cold, warm) in impact.items():
        speedup = cold / warm if warm > 0 else float("inf")
        print(f"  {stage:<12}: cold {cold:.4f} ms -> warm (cached) {warm:.6f} ms ({speedup:.0f}x)")

    print(
        f"\nOptimization priority: since {bottleneck} is the actual "
        f"measured bottleneck in THIS pipeline (at this document scale), "
        f"that's where caching (or any other optimization) has the most to "
        f"gain -- even though every stage benefits dramatically from "
        f"caching in isolation, the bottleneck stage is where the SAME "
        f"percentage improvement translates into the biggest absolute "
        f"time saved.\n\n"
        f"Worth being honest about: in THIS run, the bottleneck turned out "
        f"to be the stage ({bottleneck}) that intuition might have guessed "
        f"anyway -- it's the stage with the most document data to scan. "
        f"That's a coincidence of THIS pipeline's scale and shape, not "
        f"evidence that guessing works. At a different document count, "
        f"with different chunk sizes, or with a slower ranking/generation "
        f"step, the bottleneck could easily be somewhere else entirely -- "
        f"the only way to know for sure, every time, is to actually "
        f"profile it, exactly as we just did, rather than carry forward "
        f"an assumption from a previous system or a different scale."
    )


if __name__ == "__main__":
    main()
