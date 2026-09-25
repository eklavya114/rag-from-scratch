"""
chunk_quality.py

Turns "these chunks look bad" into actual numbers. Chunking quality is
easy to hand-wave about -- this file gives you concrete metrics so you
can measure it, compare strategies objectively, and know whether a
change you made actually improved things.
"""

import statistics

from chunking_strategies import (
    SAMPLE_DOCUMENT,
    chunk_by_fixed_size,
    chunk_by_sentences,
    chunk_by_paragraphs,
    chunk_with_overlap,
)
from chunking_comparison import starts_mid_sentence, ends_mid_sentence


def complete_sentence_ratio(chunks):
    """
    What fraction of chunks start AND end on a clean sentence boundary?
    1.0 means every chunk is a complete sentence (or sentences), with
    nothing cut off at either end. Lower is worse.
    """
    if not chunks:
        return 1.0

    complete = sum(
        1 for c in chunks
        if not starts_mid_sentence(c) and not ends_mid_sentence(c)
    )
    return complete / len(chunks)


def context_loss_score(chunks):
    """
    Estimates how much context gets lost at chunk boundaries, by
    checking how many chunks start or end mid-sentence. Each broken
    boundary counts as one point of "context loss" -- a chunk that's
    broken on both ends counts twice, since it's lost context in both
    directions.

    Returns a score from 0.0 (no context loss at all) upward -- there's
    no fixed maximum, so this is best used to compare strategies against
    each other, not as a standalone pass/fail number.
    """
    if not chunks:
        return 0.0

    broken_boundaries = sum(
        (1 if starts_mid_sentence(c) else 0) + (1 if ends_mid_sentence(c) else 0)
        for c in chunks
    )
    return broken_boundaries / len(chunks)


def size_distribution(chunks):
    """
    Reports how consistent chunk sizes are. A very high standard
    deviation relative to the mean means chunk sizes are wildly
    inconsistent -- not necessarily bad (paragraphs are naturally
    uneven), but worth knowing, since some downstream systems expect
    reasonably uniform chunk sizes.
    """
    if not chunks:
        return {"mean": 0, "stdev": 0, "min": 0, "max": 0, "coefficient_of_variation": 0}

    sizes = [len(c) for c in chunks]
    mean_size = statistics.mean(sizes)
    stdev_size = statistics.stdev(sizes) if len(sizes) > 1 else 0.0

    return {
        "mean": mean_size,
        "stdev": stdev_size,
        "min": min(sizes),
        "max": max(sizes),
        # Coefficient of variation: stdev relative to the mean. Lets you
        # compare "how spread out" sizes are across strategies with very
        # different average chunk sizes.
        "coefficient_of_variation": (stdev_size / mean_size) if mean_size else 0,
    }


def quality_report(name, chunks):
    """
    Combines all three metrics into one readable report for a single
    chunking strategy's output.
    """
    completeness = complete_sentence_ratio(chunks)
    context_loss = context_loss_score(chunks)
    sizes = size_distribution(chunks)

    print(f"--- {name} ---")
    print(f"  Chunks:                  {len(chunks)}")
    print(f"  Complete sentence ratio: {completeness:.1%}  (higher is better)")
    print(f"  Context loss score:      {context_loss:.2f}  (lower is better)")
    print(f"  Avg size:                {sizes['mean']:.1f} chars")
    print(f"  Size consistency (CV):   {sizes['coefficient_of_variation']:.2f}  (lower = more uniform)")
    print()

    return {
        "name": name,
        "completeness": completeness,
        "context_loss": context_loss,
        **sizes,
    }


def main():
    print("=== Chunk Quality Metrics ===\n")

    strategies = [
        ("Fixed-size (200 chars) -- BAD example", chunk_by_fixed_size(SAMPLE_DOCUMENT, chunk_size=200)),
        ("Fixed-size w/ overlap (200c, 50 overlap)", chunk_with_overlap(SAMPLE_DOCUMENT, chunk_size=200, overlap=50)),
        ("By sentences (3 per chunk) -- GOOD example", chunk_by_sentences(SAMPLE_DOCUMENT, sentences_per_chunk=3)),
        ("By paragraphs -- GOOD example", chunk_by_paragraphs(SAMPLE_DOCUMENT)),
    ]

    results = [quality_report(name, chunks) for name, chunks in strategies]

    best_completeness = max(results, key=lambda r: r["completeness"])
    worst_completeness = min(results, key=lambda r: r["completeness"])

    print("=" * 60)
    print(f"\nBest completeness:  {best_completeness['name']} ({best_completeness['completeness']:.1%})")
    print(f"Worst completeness: {worst_completeness['name']} ({worst_completeness['completeness']:.1%})")
    print(
        "\nThis is the numeric proof behind everything the earlier files "
        "claimed: fixed-size chunking measurably breaks more sentences and "
        "loses more context than sentence- or paragraph-based chunking. "
        "You don't have to take it on faith -- you can measure it, and use "
        "these same metrics to check any new chunking strategy you try."
    )


if __name__ == "__main__":
    main()
