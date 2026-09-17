"""
test_basic.py

Simple tests for the simple RAG system. Uses only the built-in
`unittest` module, no extra libraries needed.

Run with:
    python test_basic.py
"""

import unittest

from simple_rag import (
    DOCUMENTS,
    search_documents,
    rank_documents,
    generate_answer,
    rag_pipeline,
)


class TestRetrieval(unittest.TestCase):
    """Tests for search_documents() -- does it find the right documents?"""

    def test_finds_relevant_documents(self):
        matches = search_documents("What is RAG?", DOCUMENTS)
        titles = [m["doc"]["title"] for m in matches]
        self.assertIn("What is RAG", titles)

    def test_ignores_irrelevant_documents(self):
        matches = search_documents("What is RAG?", DOCUMENTS)
        titles = [m["doc"]["title"] for m in matches]
        # A query about RAG should not match a doc that's purely about
        # Python data types.
        self.assertNotIn("Python Data Types", titles)

    def test_no_matches_for_unrelated_query(self):
        matches = search_documents("What is the capital of France?", DOCUMENTS)
        self.assertEqual(matches, [])


class TestRanking(unittest.TestCase):
    """Tests for rank_documents() -- do the best matches come first?"""

    def test_best_match_ranks_first(self):
        matches = search_documents("What is RAG?", DOCUMENTS)
        ranked = rank_documents(matches)
        # "What is RAG" shares more words with the query than
        # "Why RAG Matters", so it should be ranked first.
        self.assertEqual(ranked[0]["title"], "What is RAG")

    def test_ranking_is_sorted_descending(self):
        matches = search_documents("vector database search", DOCUMENTS)
        ranked = rank_documents(matches)
        match_counts = [
            next(m["match_count"] for m in matches if m["doc"] is doc)
            for doc in ranked
        ]
        self.assertEqual(match_counts, sorted(match_counts, reverse=True))

    def test_empty_matches_ranks_to_empty_list(self):
        self.assertEqual(rank_documents([]), [])


class TestGeneration(unittest.TestCase):
    """Tests for generate_answer() -- does it produce sensible answers?"""

    def test_generates_answer_from_top_document(self):
        matches = search_documents("What is RAG?", DOCUMENTS)
        ranked = rank_documents(matches)
        answer = generate_answer("What is RAG?", ranked)
        self.assertIn("RAG stands for Retrieval-Augmented Generation", answer)

    def test_generates_fallback_when_no_documents(self):
        answer = generate_answer("anything", [])
        self.assertEqual(
            answer, "I don't have any information about that in my documents."
        )


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases: empty queries, no results, weird input."""

    def test_empty_query_returns_no_matches(self):
        matches = search_documents("", DOCUMENTS)
        self.assertEqual(matches, [])

    def test_empty_query_pipeline_gives_fallback_answer(self):
        answer, ranked_docs = rag_pipeline("", DOCUMENTS)
        self.assertEqual(ranked_docs, [])
        self.assertEqual(
            answer, "I don't have any information about that in my documents."
        )

    def test_query_of_only_stopwords_returns_no_matches(self):
        # "what is a" are all stopwords, so nothing should match even
        # though the query isn't technically empty.
        matches = search_documents("what is a", DOCUMENTS)
        self.assertEqual(matches, [])

    def test_pipeline_works_with_empty_document_list(self):
        answer, ranked_docs = rag_pipeline("What is RAG?", [])
        self.assertEqual(ranked_docs, [])
        self.assertEqual(
            answer, "I don't have any information about that in my documents."
        )


if __name__ == "__main__":
    unittest.main()
