"""
graceful_fallbacks.py

Decides what to return when a stage of the pipeline cannot finish, so a
user still gets something useful instead of nothing. A fallback is not
pretending nothing went wrong: each one marks the response with an
honest status ("degraded" or "partial") that tells a caller exactly how
much to trust it, the same discipline Day 22's RagResponse already used
for "ok" vs "rejected" vs "error".
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))

from basic_retriever import DOCUMENTS, Retriever  # Day 5
from practical_ranker import DOCUMENT_METADATA, PracticalRanker  # Day 6


def rank_with_fallback(retrieved, ranker):
    """
    If the ranker raises, fall back to retrieval's own order (already
    sorted by similarity, just without the extra recency/quality
    signals) rather than failing the whole request. The response is
    marked "degraded": a real answer still comes back, built on a
    slightly worse ordering than normal, not a crash or an empty result.
    """
    try:
        ranked = ranker.rank(retrieved)
        return {"ranked": ranked, "status": "ok"}
    except Exception as e:
        return {"ranked": retrieved, "status": "degraded", "reason": f"Ranker failed ({e}), fell back to retrieval order."}


def generate_with_fallback(ranked_chunks, generator_fn):
    """
    If the generator raises, fall back to returning the raw top source
    snippets directly, with an explanatory message, instead of an
    actual synthesized answer. Marked "partial": the user still gets
    real, sourced text to read, just not a generated answer built from
    it.
    """
    if not ranked_chunks:
        return {"answer": None, "sources": [], "status": "no_results", "message": "No relevant information was found for this question."}

    try:
        answer = generator_fn(ranked_chunks)
        return {"answer": answer, "sources": [c["metadata"]["title"] for c in ranked_chunks], "status": "ok"}
    except Exception as e:
        top_snippets = [
            f"{c['metadata']['title']}: {c['metadata']['text'][:120]}"
            for c in ranked_chunks[:2]
        ]
        return {
            "answer": None,
            "sources": top_snippets,
            "status": "partial",
            "message": f"The answer could not be generated ({e}), but here are the top relevant sources instead.",
        }


def retrieve_with_fallback(retriever, query, top_k):
    """If the index is genuinely empty, return 'no_results' with a helpful message directly, rather than letting retrieval return an empty list that every later stage would need to handle separately."""
    retrieved = retriever.retrieve(query, top_k=top_k)
    if not retrieved:
        return {"retrieved": [], "status": "no_results", "message": "No documents are currently indexed, or none matched this question."}
    return {"retrieved": retrieved, "status": "ok"}


def broken_generator(ranked_chunks):
    raise RuntimeError("Simulated generator failure for this demo.")


def broken_ranker_rank(self, retrieval_results):
    raise RuntimeError("Simulated ranker failure for this demo.")


def main():
    print("=== Graceful Fallbacks ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)

    query = "What is RAG?"
    retrieved = retriever.retrieve(query, top_k=3)

    print("--- 1. Ranker fails: fall back to retrieval order ---")
    broken_ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    broken_ranker.rank = broken_ranker_rank.__get__(broken_ranker)
    result = rank_with_fallback(retrieved, broken_ranker)
    print(f"status: {result['status']}")
    print(f"reason: {result.get('reason')}")
    print(f"ranked (first result): {result['ranked'][0]['metadata']['title']}\n")

    print("--- 2. Generator fails: fall back to top source snippets ---")
    ranked = ranker.rank(retrieved)
    result = generate_with_fallback(ranked, broken_generator)
    print(f"status: {result['status']}")
    print(f"message: {result['message']}")
    print(f"sources: {result['sources']}\n")

    print("--- 3. Generator succeeds: a real answer, for comparison ---")
    def working_generator(ranked_chunks):
        top = ranked_chunks[0]
        return f"Based on \"{top['metadata']['title']}\": {top['metadata']['text'][:100]}"
    result = generate_with_fallback(ranked, working_generator)
    print(f"status: {result['status']}")
    print(f"answer: {result['answer']}\n")

    print("--- 4. Index is empty: no_results with a helpful message ---")
    empty_retriever = Retriever()  # never indexed, so its DB has nothing in it
    result = retrieve_with_fallback(empty_retriever, query, top_k=3)
    print(f"status: {result['status']}")
    print(f"message: {result['message']}\n")

    print(
        "Why users getting something useful instead of nothing matters: "
        "a 'degraded' ranking still uses the retriever's own relevance "
        "ordering, which is usually still reasonably good on its own, "
        "just missing the extra recency and quality signals. A 'partial' "
        "answer still hands over real, sourced text a user can read "
        "themselves, instead of a blank error. Neither of these pretends "
        "everything worked, the honest status says exactly what "
        "happened, but neither one leaves the user with literally "
        "nothing just because one internal stage had a problem."
    )


if __name__ == "__main__":
    main()
