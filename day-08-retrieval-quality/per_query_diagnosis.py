"""
per_query_diagnosis.py

metric_analysis.py found that "How do I store embeddings for fast
lookup?" (NDCG@3 = 0.63) was the worst-performing query in our dataset.
This file digs into exactly WHY, using the real Day 5 retriever and Day
2's embedding function -- not a hypothetical example.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS
from comparison import text_to_embedding, cosine_similarity, CONCEPTS  # Day 2
from evaluation_framework import unique_doc_ids_in_order


def show_retrieved_vs_expected(query, retriever, relevant_ids, k=6):
    """
    WHAT WAS RETRIEVED VS. WHAT SHOULD HAVE BEEN: the most basic
    diagnostic step -- just look at both lists side by side. Half of
    debugging a bad retrieval result is simply seeing it clearly instead
    of only looking at the aggregate score.
    """
    results = retriever.retrieve(query, top_k=k)
    ranked_ids = unique_doc_ids_in_order(results)

    print(f'Query: "{query}"')
    print(f"Expected relevant document id(s): {relevant_ids}\n")

    print("Actually retrieved (in order):")
    for i, result in enumerate(results, start=1):
        doc_id = result["metadata"]["doc_id"]
        title = result["metadata"]["title"]
        marker = " <-- RELEVANT" if doc_id in relevant_ids else ""
        print(f"  #{i}: doc_id={doc_id} \"{title}\" (similarity={result['similarity']:.3f}){marker}")

    return results, ranked_ids


def analyze_query_embedding(query):
    """
    ANALYZE THE EMBEDDING: shows exactly which concept dimensions the
    query activated. Since Day 2's embeddings are a transparent bag-of-
    concepts (not a black-box neural embedding), we can literally read
    off why a query matched or didn't match -- a real production system
    would need a different technique (inspecting nearest neighbors,
    probing dimensions) to get the same visibility.
    """
    embedding = text_to_embedding(query)
    print(f"Query embedding: {embedding}")
    print("Concept activations:")
    for concept_name, score in zip(CONCEPTS.keys(), embedding):
        marker = " (active)" if score > 0 else ""
        print(f"  {concept_name:16s}: {score:.1f}{marker}")


def compare_query_to_document(query, document):
    """
    Shows word-by-word why a query and a specific document scored the
    similarity they did -- which words in the query actually landed on a
    concept the document also touches, and which didn't match anything.

    NOTE: this compares against the document's FULL text, while the
    retriever above actually indexes and scores individual CHUNKS (Day
    4's chunking). So the similarity printed here won't exactly match
    any single similarity number in the "Actually retrieved" list above
    -- it's a close approximation useful for understanding the concept
    overlap, not a re-derivation of the retriever's exact chunk score.
    """
    query_words = set(w.strip("?.,!").lower() for w in query.split())
    doc_text = document["title"] + " " + document["text"]
    doc_words = set(w.strip("?.,!").lower() for w in doc_text.split())

    print(f'Comparing query to "{document["title"]}":')
    for concept_name, concept_words in CONCEPTS.items():
        query_hits = query_words & set(concept_words)
        doc_hits = doc_words & set(concept_words)
        if query_hits or doc_hits:
            print(f"  {concept_name:16s}: query touches {query_hits or '{}'}, document touches {doc_hits or '{}'}")

    similarity = cosine_similarity(text_to_embedding(query), text_to_embedding(doc_text))
    print(f"  -> cosine similarity: {similarity:.3f}")


def diagnose(query, relevant_ids, retriever):
    """Runs the full diagnostic sequence for one failing query."""
    print("=" * 60)
    results, ranked_ids = show_retrieved_vs_expected(query, retriever, relevant_ids)
    print()

    print("--- Query embedding analysis ---")
    analyze_query_embedding(query)
    print()

    expected_doc = next(d for d in DOCUMENTS if d["id"] in relevant_ids)
    print("--- Why the query did/didn't match the EXPECTED document ---")
    compare_query_to_document(query, expected_doc)
    print()

    top_result_doc_id = ranked_ids[0] if ranked_ids else None
    if top_result_doc_id and top_result_doc_id not in relevant_ids:
        wrong_doc = next(d for d in DOCUMENTS if d["id"] == top_result_doc_id)
        print(f"--- Why the TOP result (\"{wrong_doc['title']}\") outranked the expected document ---")
        compare_query_to_document(query, wrong_doc)
        print()

    return top_result_doc_id in relevant_ids if ranked_ids else False


def suggest_fix(query, relevant_ids, top_result_relevant):
    print("--- Diagnosis summary ---")
    if top_result_relevant:
        print(
            "  The correct document WAS ranked first -- if NDCG is still "
            "lower than expected, the issue is likely a SECOND relevant "
            "document (graded relevance) not being found high enough, "
            "rather than the top result being wrong."
        )
    else:
        print(
            "  The correct document was NOT ranked first. Likely cause: "
            "the query's wording doesn't activate the same concept "
            "dimensions as the expected document's text. This is a "
            "CHUNKING/EMBEDDING gap, not a bug -- the fake concept "
            "vocabulary (Day 2) simply doesn't include every word a user "
            "might phrase a question with. A real embedding model, "
            "trained on much more text, would generalize past this; our "
            "fixed concept list can't. The practical fix within THIS "
            "project: expand the concept vocabulary (as we did repeatedly "
            "on Days 2-7 when a demo query didn't match), or apply query "
            "expansion (Day 5's query_preprocessing.py) before retrieval."
        )


def main():
    print("=== Per-Query Diagnosis: Debugging a Specific Failure ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    # The worst-performing query identified by metric_analysis.py.
    query = "How do I store embeddings for fast lookup?"
    relevant_ids = {3}  # "What is a Vector Database"

    top_result_relevant = diagnose(query, relevant_ids, retriever)
    suggest_fix(query, relevant_ids, top_result_relevant)


if __name__ == "__main__":
    main()
