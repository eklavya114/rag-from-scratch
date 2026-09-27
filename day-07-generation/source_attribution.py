"""
source_attribution.py

An answer without clear sourcing is hard to trust and impossible to
verify. This file tracks exactly which chunk backed which claim, quotes
the relevant text, attaches confidence, and handles the case where there
are no good sources at all.
"""


def attribute_claims(claims_with_sources):
    """
    Takes a list of (claim_text, source_chunk) pairs and builds an
    attributed answer: each claim immediately followed by which source
    supports it. This is more precise than a single source list at the
    end of an answer -- it tells you exactly WHICH sentence came from
    WHICH source, not just that the sources were used somewhere.
    """
    lines = []
    for claim_text, source_chunk in claims_with_sources:
        title = source_chunk["metadata"]["title"]
        lines.append(f"{claim_text} [Source: {title}]")
    return " ".join(lines)


def quote_relevant_section(chunk, max_quote_length=100):
    """
    Pulls a short, direct quote from a source chunk, rather than just
    naming the source. A named source tells you WHERE a claim came from;
    an actual quote lets you verify WHAT it actually says, without
    having to go find the original document yourself.
    """
    text = chunk["metadata"]["text"]
    if len(text) <= max_quote_length:
        return text
    # Truncate at the nearest word boundary rather than mid-word, so the
    # quote doesn't end on a fragment like "inform..."
    truncated = text[:max_quote_length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def build_citation_link(chunk, doc_url_map):
    """
    Builds a clickable citation reference, if a URL is known for the
    source document. Falls back to a plain title reference when no URL
    exists -- citations shouldn't disappear just because a document
    doesn't happen to have a link.
    """
    title = chunk["metadata"]["title"]
    doc_id = chunk["metadata"].get("doc_id")
    url = doc_url_map.get(doc_id)
    if url:
        return f"[{title}]({url})"
    return f"[{title}]"


def document_confidence(chunk):
    """
    Reuses whatever relevance score the chunk already carries
    (similarity from Day 5, or final_score from Day 6's ranking) as a
    per-source confidence indicator, so a reader can tell which cited
    source the system was MOST sure about, not just that it was cited.
    """
    return chunk.get("final_score", chunk.get("similarity", 0.0))


def generate_attributed_answer(query, ranked_chunks, doc_url_map=None):
    """
    Puts it all together: an answer where every source is quoted, linked
    (if possible), and confidence-scored. Handles the no-sources case
    explicitly, since an attribution system that silently produces an
    empty or misleading answer defeats the entire point of attribution.
    """
    doc_url_map = doc_url_map or {}

    if not ranked_chunks:
        return (
            f'I don\'t have any sourced information to answer "{query}". '
            f"Rather than guess, I'm telling you directly: no relevant "
            f"documents were found."
        )

    lines = [f'Regarding "{query}":\n']
    for chunk in ranked_chunks:
        quote = quote_relevant_section(chunk)
        citation = build_citation_link(chunk, doc_url_map)
        confidence = document_confidence(chunk)
        lines.append(f'  "{quote}" -- {citation} (confidence: {confidence:.0%})')

    return "\n".join(lines)


def main():
    print("=== Source Attribution Demo ===\n")

    ranked_chunks = [
        {
            "metadata": {
                "doc_id": 2,
                "title": "What is RAG",
                "text": "RAG stands for Retrieval-Augmented Generation. It retrieves "
                        "relevant documents before generating an answer, instead of "
                        "relying only on what a language model memorized.",
            },
            "final_score": 0.92,
        },
        {
            "metadata": {
                "doc_id": 5,
                "title": "Why RAG Matters",
                "text": "RAG matters because language models can be outdated.",
            },
            "final_score": 0.65,
        },
    ]

    query = "What is RAG?"

    print("--- 1. Claim-level attribution ---")
    claims = [
        ("RAG combines retrieval with generation.", ranked_chunks[0]),
        ("It helps overcome outdated model knowledge.", ranked_chunks[1]),
    ]
    print(attribute_claims(claims))
    print()

    print("--- 2. Quoting a long source ---")
    print(quote_relevant_section(ranked_chunks[0], max_quote_length=60))
    print()

    print("--- 3. Citation links (with and without a known URL) ---")
    doc_url_map = {2: "https://example.com/docs/what-is-rag"}
    for chunk in ranked_chunks:
        print(f"  {build_citation_link(chunk, doc_url_map)}")
    print()

    print("--- 4. Full attributed answer ---")
    print(generate_attributed_answer(query, ranked_chunks, doc_url_map))
    print()

    print("--- 5. No sources available (edge case) ---")
    print(generate_attributed_answer("What's the weather today?", []))

    print(
        "\nWhy attribution matters: an answer that says 'RAG helps overcome "
        "outdated knowledge' is a claim you either have to trust blindly or "
        "not at all. An answer that says the SAME thing but points to "
        "exactly which source, with a quote and a confidence score, gives "
        "you a way to verify it yourself -- which is the entire point of "
        "grounding answers in real documents instead of a model's memory."
    )


if __name__ == "__main__":
    main()
