"""
hybrid_retrieval.py

Day 1 showed keyword search: fast, simple, but only finds exact word
matches. Days 2-3 showed embedding search: finds documents by meaning,
even with different wording, but can occasionally rank things in
surprising ways since it only understands a handful of hand-picked
concepts.

Hybrid retrieval runs both and combines their results, so a chunk that
either method alone would have missed still has a chance to surface.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


STOPWORDS = {
    "what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for",
    "how", "do", "does", "i", "up", "by", "be", "it", "its", "on", "at", "as",
}


def keyword_search_chunks(query, chunks, top_k=3):
    """
    Day 1-style keyword search, applied to CHUNKS instead of whole
    documents, so it can be compared fairly against embedding search
    (which also operates on chunks in this project).

    Uses whole-word matching (a set of words, not substring checks) --
    the same fix we made back on Day 2 after finding that naive
    substring matching produces false positives.
    """
    query_words = [w.strip("?.,!") for w in query.lower().split()]
    query_words = [w for w in query_words if w and w not in STOPWORDS]

    scored = []
    for chunk in chunks:
        chunk_words = set(w.strip("?.,!") for w in chunk["text"].lower().split())
        match_count = sum(1 for word in query_words if word in chunk_words)
        if match_count > 0:
            scored.append((chunk, match_count))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]


def build_chunk_list(documents):
    """
    Splits every document into chunks the same way basic_retriever.py
    does, but keeps them as plain dicts (not embedded/stored yet) so
    keyword_search_chunks() can search the raw text directly.
    """
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-04-chunking"))
    from chunking_strategies import chunk_by_paragraphs

    chunk_list = []
    for doc in documents:
        for chunk_index, chunk_text in enumerate(chunk_by_paragraphs(doc["text"])):
            chunk_list.append({
                "doc_id": doc["id"],
                "title": doc["title"],
                "chunk_index": chunk_index,
                "text": chunk_text,
            })
    return chunk_list


def hybrid_search(query, retriever, chunks, top_k=3, keyword_weight=0.4, semantic_weight=0.6):
    """
    Runs both keyword and embedding search, then combines their scores
    into one ranking. Each method's score gets normalized to a 0-1 range
    first (since keyword match counts and cosine similarities aren't on
    the same scale), then combined with the given weights.
    """
    keyword_results = keyword_search_chunks(query, chunks, top_k=len(chunks))
    semantic_results = retriever.retrieve(query, top_k=len(chunks))

    max_keyword_score = max((score for _, score in keyword_results), default=1)

    combined_scores = {}  # (doc_id, chunk_index) -> combined score

    for chunk, score in keyword_results:
        key = (chunk["doc_id"], chunk["chunk_index"])
        normalized = score / max_keyword_score if max_keyword_score else 0
        combined_scores[key] = combined_scores.get(key, 0) + normalized * keyword_weight

    for result in semantic_results:
        key = (result["metadata"]["doc_id"], result["metadata"]["chunk_index"])
        # Cosine similarity is already roughly 0-1 for our fake embeddings.
        combined_scores[key] = combined_scores.get(key, 0) + result["similarity"] * semantic_weight

    # Look up chunk text/title for the final combined results.
    chunk_lookup = {(c["doc_id"], c["chunk_index"]): c for c in chunks}
    ranked = sorted(combined_scores.items(), key=lambda pair: pair[1], reverse=True)

    results = []
    for key, score in ranked[:top_k]:
        chunk = chunk_lookup[key]
        results.append({"title": chunk["title"], "chunk_index": chunk["chunk_index"], "score": score})
    return results


def main():
    print("=== Hybrid Retrieval: Keyword + Semantic ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    chunks = build_chunk_list(DOCUMENTS)

    # A query with an exact keyword match AND a query where keyword and
    # semantic search genuinely disagree -- keyword search only matches
    # the one chunk containing "embeddings" literally, while semantic
    # search also picks up RAG-related chunks through shared concepts
    # ("lookup" maps to the same "retrieval" concept as "retrieves").
    # This is the case that actually shows hybrid combining what each
    # method finds on its own.
    queries = [
        "What is RAG?",
        "lookup embeddings quick",
    ]

    for query in queries:
        print(f"Query: \"{query}\"\n")

        keyword_only = keyword_search_chunks(query, chunks, top_k=3)
        print("  Keyword-only results:")
        if keyword_only:
            for chunk, score in keyword_only:
                print(f"    {chunk['title']:20s} chunk {chunk['chunk_index']} (matched {score} word(s))")
        else:
            print("    (no results -- no exact word overlap)")

        semantic_only = retriever.retrieve(query, top_k=3)
        print("  Semantic-only results:")
        for result in semantic_only:
            title = result["metadata"]["title"]
            chunk_idx = result["metadata"]["chunk_index"]
            print(f"    {title:20s} chunk {chunk_idx} (similarity {result['similarity']:.3f})")

        hybrid_results = hybrid_search(query, retriever, chunks, top_k=3)
        print("  Hybrid results:")
        for result in hybrid_results:
            print(f"    {result['title']:20s} chunk {result['chunk_index']} (combined score {result['score']:.3f})")

        print()

    print("=" * 60)
    print(
        "\nTradeoffs: keyword search is fast and precise for exact terms, but "
        "misses paraphrased queries entirely. Semantic search catches "
        "paraphrasing but can occasionally misjudge similarity based on which "
        "hand-picked concepts a query happens to touch. Hybrid search costs "
        "more (running both), but a document that either method would rank "
        "highly gets a real chance to surface in the final results -- it "
        "doesn't depend on a single method getting it right alone."
    )


if __name__ == "__main__":
    main()
