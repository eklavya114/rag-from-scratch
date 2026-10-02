"""
quality_analysis_by_context.py

Measures answer quality as the NUMBER of documents included in context
grows, using Day 7's answer_quality.py checks on a template-generated
answer. The goal: find where quality plateaus (or actively drops) as
more, less-relevant material gets added -- proving "more context" isn't
automatically "better answer."
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))
from answer_quality import answers_the_question, _keywords  # Day 7
from context_budget_calculator import estimate_tokens


def topical_relevance_density(query, documents):
    """
    Day 7's factual_consistency() checks whether the answer's words
    appear SOMEWHERE in the sources -- which can't meaningfully drop
    here, since our generator just concatenates source text verbatim
    (every word trivially IS grounded in a source, even an irrelevant
    one). What we actually need to measure for THIS question -- does
    adding more documents dilute the answer with off-topic content -- is
    different: what fraction of the TOTAL answer is made up of content
    from documents that actually relate to the query, versus documents
    that don't.

    We approximate "relates to the query" the same way Day 7 measures
    query relevance: keyword overlap with the query. A document sharing
    no keywords with the query contributes words to the final answer
    that have nothing to do with what was asked -- diluting the signal
    even though every individual word is still technically "grounded."
    """
    query_words = _keywords(query)
    total_words = 0
    on_topic_words = 0

    for doc in documents:
        doc_words = _keywords(doc["text"])
        word_count = len(doc["text"].split())
        total_words += word_count
        if query_words & doc_words:
            on_topic_words += word_count

    return on_topic_words / total_words if total_words else 1.0


QUERY = "What is RAG?"

# Ordered by DECREASING relevance to the query -- the first couple are
# genuinely about RAG, the rest drift further and further off-topic.
# This mirrors a real retrieval result list: the top few are strong
# matches, and quality honestly degrades further down the ranking.
DOCUMENTS_BY_RELEVANCE = [
    {"title": "What is RAG", "text": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents before generating an answer."},
    {"title": "Why RAG Matters", "text": "RAG matters because language models can be outdated. Retrieval lets them use fresh information."},
    {"title": "Vector Databases", "text": "A vector database stores embeddings and allows fast similarity search across large collections."},
    {"title": "Chunking Basics", "text": "Chunking splits documents into smaller pieces so they fit well in embeddings and retrieval."},
    {"title": "Python Data Types", "text": "Python has several built-in data types including strings, integers, floats, lists, and dictionaries."},
    {"title": "Keyword Search", "text": "Keyword search finds documents with exact matching words but misses different phrasing."},
]


def generate_answer_from_documents(query, documents):
    """
    A simple concatenation-style generator (same idea as Day 7's
    simple_generator.py): stitches together what the included documents
    say. As more, less-relevant documents get added, their text still
    gets concatenated in -- which is exactly how irrelevant material can
    dilute an otherwise good answer in a real system too.
    """
    parts = [f'Regarding "{query}":']
    for doc in documents:
        parts.append(doc["text"])
    return " ".join(parts)


def measure_quality_at_each_count(query, documents):
    results = []
    for count in range(1, len(documents) + 1):
        included = documents[:count]
        answer = generate_answer_from_documents(query, included)

        _, relevance_score = answers_the_question(query, answer)
        density_score = topical_relevance_density(query, included)
        token_cost = estimate_tokens(answer)

        results.append({
            "count": count,
            "relevance_score": relevance_score,
            "density_score": density_score,
            "token_cost": token_cost,
            "titles": [d["title"] for d in included],
        })
    return results


def find_optimal_count(results, quality_key="density_score"):
    """
    FIND THE OPTIMAL DOCUMENT COUNT: simply the count with the single
    highest quality score. Unlike a metric that can only ever increase,
    topical_relevance_density() can genuinely PEAK and then decline once
    off-topic documents start getting added -- so "optimal" here really
    can be smaller than "all of them."
    """
    best = max(results, key=lambda r: r[quality_key])
    return best["count"], best[quality_key]


def main():
    print("=== Quality Analysis by Context Size ===\n")
    print(f"Query: \"{QUERY}\"\n")

    results = measure_quality_at_each_count(QUERY, DOCUMENTS_BY_RELEVANCE)

    header = f"{'# Docs':>6} | {'Tokens':>6} | {'Relevance':>9} | {'Topic Density':>13} | {'Documents included'}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['count']:>6} | {r['token_cost']:>6} | {r['relevance_score']:>9.2f} | {r['density_score']:>13.2f} | {', '.join(r['titles'])}")

    optimal_count, peak_quality = find_optimal_count(results, "density_score")

    print(f"\nPeak topical relevance density: {peak_quality:.2f}")
    print(f"Document count that reaches it: {optimal_count}")

    final = results[-1]
    optimal = results[optimal_count - 1]
    tokens_saved = final["token_cost"] - optimal["token_cost"]

    print(
        f"\nUsing all {len(DOCUMENTS_BY_RELEVANCE)} documents costs {final['token_cost']} tokens for a "
        f"topical density of {final['density_score']:.2f}.\n"
        f"Using just the top {optimal_count} document(s) costs {optimal['token_cost']} tokens for a "
        f"topical density of {optimal['density_score']:.2f} -- "
        f"saving {tokens_saved} tokens ({tokens_saved/final['token_cost']:.0%}) for "
        f"{'better' if optimal['density_score'] > final['density_score'] else 'the same'} on-topic focus."
    )

    print(
        "\nWhy quality doesn't just keep climbing: once documents stop "
        "sharing any keywords with the actual question (Python data "
        "types, generic keyword search basics -- neither mentions "
        "'RAG'), every word they contribute to the concatenated answer is "
        "pure dilution: real words, grounded in a real source, but "
        "irrelevant to what was actually asked. Note that the 'relevance' "
        "check stays at 1.00 throughout, because the genuinely relevant "
        "first sentence never leaves the answer -- that's exactly why a "
        "single relevance check isn't enough on its own. It tells you the "
        "answer ISN'T completely off-topic; it says nothing about how "
        "much of the answer is being wasted on material that is."
    )


if __name__ == "__main__":
    main()
