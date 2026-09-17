"""
examples.py

Five real examples of running queries through the simple RAG system.
Each one shows the question, the answer, and a comment on what actually
happened under the hood -- including the cases where it fails gracefully
or gets confused by an ambiguous question.
"""

from simple_rag import DOCUMENTS, rag_pipeline


def run_example(number, query):
    print(f"--- Example {number} ---")
    print(f"Query: {query}")

    answer, ranked_docs = rag_pipeline(query, DOCUMENTS)

    print(f"Retrieved (best first): {[d['title'] for d in ranked_docs]}")
    print(f"Answer: {answer}\n")


def main():
    # Example 1: A clear question about Python.
    # What happens: "python" is a strong keyword, so the two Python docs
    # both match and get ranked above everything else.
    run_example(1, "What is Python used for?")

    # Example 2: A question about RAG itself.
    # What happens: "rag" matches both the "What is RAG" doc and the
    # "Why RAG Matters" doc, and the more direct one ranks first.
    run_example(2, "What is RAG?")

    # Example 3: A question about vector databases.
    # What happens: "vector" and "database" both appear in doc 3, so it
    # matches with a high score and comes back as the top (and really
    # only relevant) result.
    run_example(3, "How does a vector database work?")

    # Example 4: A question about something NOT in our documents at all.
    # What happens: none of the query words show up in any document, so
    # search_documents() returns zero matches, and generate_answer()
    # honestly says it doesn't know, instead of making something up.
    run_example(4, "What is the capital of France?")

    # Example 5: An ambiguous question that could match multiple topics.
    # What happens: "search" shows up in the keyword search doc, but the
    # word could also relate to vector search. Since our system only does
    # exact keyword matching, it picks whichever doc has the most word
    # overlap -- it doesn't actually understand the ambiguity, it just
    # counts words. This is a good example of why real RAG systems use
    # embeddings instead of plain keyword matching.
    run_example(5, "How does search work?")


if __name__ == "__main__":
    main()
