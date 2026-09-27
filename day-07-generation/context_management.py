"""
context_management.py

A real LLM has a limited context window -- only so much text fits in one
prompt. If retrieval and ranking hand back more material than fits, you
have to make deliberate choices about what to keep, what to cut, and
what to shrink. This file shows those choices concretely.

We measure "space" in characters here, as a simple stand-in for tokens --
the exact unit doesn't matter for the concept, just that it's a hard
limit you have to respect.
"""


def estimate_size(text):
    """A simple proxy for 'how much context window space does this use.'"""
    return len(text)


def select_top_chunks_by_budget(ranked_chunks, max_total_chars):
    """
    SELECT MOST RELEVANT CHUNKS WHEN SPACE IS LIMITED: walks down the
    ranked list (best first) and keeps adding chunks until the next one
    would blow the budget, then stops. Since the list is already ranked
    by relevance, this greedily keeps the best material and drops the
    least relevant -- exactly the tradeoff you want when you can't fit
    everything.
    """
    selected = []
    total_size = 0

    for chunk in ranked_chunks:
        chunk_size = estimate_size(chunk["metadata"]["text"])
        if total_size + chunk_size > max_total_chars:
            continue  # skip this one, but keep checking smaller ones below it
        selected.append(chunk)
        total_size += chunk_size

    return selected


def summarize_chunk(chunk, max_length=80):
    """
    SUMMARIZE LONG DOCUMENTS TO FIT: a crude extractive summary -- just
    the first sentence (or a truncated version of it), on the
    assumption that the first sentence of a well-written chunk usually
    carries the main point. A real system might use an LLM to summarize
    properly; this keeps the same SHAPE of solution (shrink a long chunk
    down to its core point) without needing one.
    """
    text = chunk["metadata"]["text"]
    first_sentence = text.split(". ")[0]
    if not first_sentence.endswith("."):
        first_sentence += "."

    if len(first_sentence) > max_length:
        truncated = first_sentence[:max_length].rsplit(" ", 1)[0]
        return truncated + "..."
    return first_sentence


def reorder_by_importance(chunks, importance_key="final_score"):
    """
    REORDER DOCUMENTS BY IMPORTANCE: some LLMs pay more attention to
    information at the START and END of a long context than the middle
    (a well-documented effect). Given a fixed set of chunks we've
    already decided to include, this places the most important ones
    first and last, with lower-importance ones buried in the middle --
    trying to work with that attention pattern instead of against it.
    """
    sorted_chunks = sorted(chunks, key=lambda c: c.get(importance_key, 0), reverse=True)

    if len(sorted_chunks) <= 2:
        return sorted_chunks

    # Interleave: best chunk first, second-best last, then fill the
    # middle with the rest in descending order.
    reordered = [sorted_chunks[0]]
    middle = sorted_chunks[2:]
    reordered.extend(middle)
    reordered.append(sorted_chunks[1])
    return reordered


def extract_key_sentences(chunk, keywords):
    """
    EXTRACT KEY INFORMATION BEFORE PASSING TO GENERATOR: pulls out only
    the sentences that actually mention one of the given keywords,
    instead of passing an entire chunk when only part of it is relevant
    to the current query. This trims context size while keeping exactly
    the parts most likely to matter.
    """
    text = chunk["metadata"]["text"]
    # Splitting on ". " strips the trailing period from every sentence
    # EXCEPT the last one (which keeps it, since there's no following
    # ". " to split on). Stripping any trailing period here normalizes
    # that, so rejoining with ". " + a single final "." doesn't produce
    # a double period on the last matched sentence.
    sentences = [s.strip().rstrip(".") for s in text.split(". ") if s.strip()]

    matching = [
        s for s in sentences
        if any(keyword.lower() in s.lower() for keyword in keywords)
    ]
    return ". ".join(matching) + ("." if matching else "")


def handle_large_document_set(all_chunks, max_total_chars, max_chunks=5):
    """
    HANDLE VERY LARGE DOCUMENT SETS: combines the techniques above into
    one practical pipeline -- cap the NUMBER of chunks first (a hard
    ceiling regardless of size), then fit what's left into the character
    budget. Two limits instead of one, because a huge number of tiny
    chunks can still overwhelm a prompt even if each one is small.
    """
    capped = all_chunks[:max_chunks]
    return select_top_chunks_by_budget(capped, max_total_chars)


def main():
    print("=== Context Management Demo ===\n")

    ranked_chunks = [
        {
            "metadata": {"title": "What is RAG", "text": "RAG stands for Retrieval-Augmented Generation. "
                         "It retrieves relevant documents before generating an answer. "
                         "This helps ground answers in real, current information."},
            "final_score": 0.95,
        },
        {
            "metadata": {"title": "Why RAG Matters", "text": "RAG matters because language models can be "
                         "outdated or lack private data. Retrieval lets them use fresh, specific "
                         "information without needing to be retrained from scratch."},
            "final_score": 0.80,
        },
        {
            "metadata": {"title": "What is a Vector Database", "text": "A vector database stores data as "
                         "numerical vectors called embeddings, allowing fast similarity search "
                         "across huge collections of documents."},
            "final_score": 0.55,
        },
        {
            "metadata": {"title": "Keyword Search Basics", "text": "Keyword search finds documents that "
                         "contain the exact words in a query, but misses documents using different "
                         "words for the same idea."},
            "final_score": 0.30,
        },
    ]

    print("--- 1. Selecting chunks within a character budget ---")
    total_available = sum(estimate_size(c["metadata"]["text"]) for c in ranked_chunks)
    budget = 200
    selected = select_top_chunks_by_budget(ranked_chunks, max_total_chars=budget)
    print(f"Total available: {total_available} chars. Budget: {budget} chars.")
    print(f"Selected {len(selected)} of {len(ranked_chunks)} chunks:")
    for c in selected:
        print(f"  {c['metadata']['title']} ({estimate_size(c['metadata']['text'])} chars)")
    print()

    print("--- 2. Summarizing a long chunk ---")
    for c in ranked_chunks[:2]:
        print(f"  Full:    {c['metadata']['text']}")
        print(f"  Summary: {summarize_chunk(c)}")
        print()

    print("--- 3. Reordering by importance (best-first-and-last) ---")
    reordered = reorder_by_importance(ranked_chunks)
    for i, c in enumerate(reordered, start=1):
        print(f"  Position {i}: {c['metadata']['title']} (score {c['final_score']})")
    print()

    print("--- 4. Extracting only relevant sentences ---")
    long_chunk = {
        "metadata": {
            "title": "Why RAG Matters",
            "text": "RAG matters because language models can be outdated. Some models also "
                    "cost a lot to run at scale. Retrieval lets them use fresh, specific "
                    "information without needing to be retrained.",
        }
    }
    extracted = extract_key_sentences(long_chunk, keywords=["outdated", "retrained"])
    print(f"  Full text: {long_chunk['metadata']['text']}")
    print(f"  Extracted: {extracted}")
    print()

    print("--- 5. Handling a large document set (cap count + size together) ---")
    handled = handle_large_document_set(ranked_chunks, max_total_chars=180, max_chunks=2)
    print(f"  Kept {len(handled)} chunk(s) after capping at 2 chunks AND 180 chars:")
    for c in handled:
        print(f"    {c['metadata']['title']}")

    print(
        "\nThe common thread: context window space is a real, hard "
        "constraint, and every one of these techniques is really about "
        "the same tradeoff -- deciding what to keep when you can't keep "
        "everything, using the ranking you already have (Day 6) to make "
        "that decision as informed as possible instead of arbitrary."
    )


if __name__ == "__main__":
    main()
