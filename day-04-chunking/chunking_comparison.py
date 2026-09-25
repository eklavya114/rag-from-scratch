"""
chunking_comparison.py

Runs all 5 chunking strategies from chunking_strategies.py on the same
document, and measures real tradeoffs: how many chunks each produces,
how big they are on average, and how often they cut a sentence in half.
"""

import re
import statistics

from chunking_strategies import (
    SAMPLE_DOCUMENT,
    chunk_by_fixed_size,
    chunk_by_tokens,
    chunk_by_sentences,
    chunk_by_paragraphs,
    chunk_with_overlap,
)


def ends_mid_sentence(chunk):
    """
    Checks whether a chunk cuts off in the middle of a sentence, instead
    of ending cleanly on punctuation. A rough but useful signal: if the
    last non-whitespace character isn't ., !, or ?, the chunk almost
    certainly stopped mid-thought.
    """
    stripped = chunk.strip()
    if not stripped:
        return False
    return stripped[-1] not in ".!?"


def starts_mid_sentence(chunk):
    """
    Checks whether a chunk starts partway through a sentence, rather
    than at the beginning of one. If the first letter is lowercase, it's
    very likely a continuation of a sentence that started in the
    previous chunk.
    """
    stripped = chunk.strip()
    if not stripped:
        return False
    first_letter = next((c for c in stripped if c.isalpha()), None)
    return first_letter is not None and first_letter.islower()


def analyze_chunks(name, chunks):
    """
    Computes summary stats for one chunking method's output: chunk
    count, average/min/max size, and how many chunks broke a sentence
    at either end.
    """
    sizes = [len(c) for c in chunks]
    broken_start = sum(1 for c in chunks if starts_mid_sentence(c))
    broken_end = sum(1 for c in chunks if ends_mid_sentence(c))

    return {
        "name": name,
        "num_chunks": len(chunks),
        "avg_size": statistics.mean(sizes) if sizes else 0,
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
        "broken_sentences": broken_start + broken_end,
    }


def print_summary_table(results):
    header = f"{'Strategy':<32} | {'Chunks':>6} | {'Avg Size':>8} | {'Min':>5} | {'Max':>5} | {'Broken Sentences':>16}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['name']:<32} | "
            f"{r['num_chunks']:>6} | "
            f"{r['avg_size']:>8.1f} | "
            f"{r['min_size']:>5} | "
            f"{r['max_size']:>5} | "
            f"{r['broken_sentences']:>16}"
        )


def main():
    print("=== Chunking Strategy Comparison ===\n")
    print(f"Document length: {len(SAMPLE_DOCUMENT)} characters, "
          f"{len(SAMPLE_DOCUMENT.split())} words\n")

    strategies = [
        ("Fixed-size (200 chars)", chunk_by_fixed_size(SAMPLE_DOCUMENT, chunk_size=200)),
        ("By tokens (40 words)", chunk_by_tokens(SAMPLE_DOCUMENT, tokens_per_chunk=40)),
        ("By tokens w/ overlap (40w, 10 overlap)", chunk_by_tokens(SAMPLE_DOCUMENT, tokens_per_chunk=40, overlap_tokens=10)),
        ("By sentences (3 per chunk)", chunk_by_sentences(SAMPLE_DOCUMENT, sentences_per_chunk=3)),
        ("By paragraphs", chunk_by_paragraphs(SAMPLE_DOCUMENT)),
        ("Fixed-size w/ overlap (200c, 50 overlap)", chunk_with_overlap(SAMPLE_DOCUMENT, chunk_size=200, overlap=50)),
    ]

    results = [analyze_chunks(name, chunks) for name, chunks in strategies]
    print_summary_table(results)

    print(
        "\nWhat to notice:\n"
        "- Fixed-size chunking (with or without overlap) breaks sentences "
        "constantly, because it doesn't look at the text at all -- it just "
        "counts characters.\n"
        "- Token-based chunking breaks sentences less often, but still can, "
        "since it counts words rather than respecting punctuation.\n"
        "- Sentence-based and paragraph-based chunking break zero sentences, "
        "because they're built around sentence/paragraph boundaries by "
        "design.\n"
        "- The cost of that improvement: sentence and paragraph chunks vary "
        "more in size, since real sentences and paragraphs aren't uniform "
        "length. Fixed-size chunking trades chunk quality for predictable, "
        "uniform chunk sizes.\n\n"
        "When to use which:\n"
        "- Fixed-size: quick prototypes, or when uniform chunk size matters "
        "more than readability (e.g. hitting a strict token limit).\n"
        "- Token-based with overlap: a solid default for most RAG systems -- "
        "predictable size, and overlap helps recover some lost context.\n"
        "- Sentence/paragraph-based: best when chunk readability and "
        "coherence matter most, like FAQs or well-structured articles."
    )


if __name__ == "__main__":
    main()
