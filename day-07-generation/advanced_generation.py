"""
advanced_generation.py

Six more sophisticated generation behaviors beyond a plain answer:
combining multiple sources into one synthesis, handling sources that
disagree, expressing real uncertainty, asking for clarification, and
producing structured output like tables and comparisons.
"""


def multi_document_synthesis(query, ranked_chunks):
    """
    MULTI-DOCUMENT SYNTHESIS: combines information from several sources
    into ONE coherent statement, rather than listing them separately
    (like simple_generator.py's concatenation approach). This is a
    template-based stand-in for what an LLM would do more fluidly, but
    it demonstrates the same goal: weave separate facts into one answer.
    """
    if not ranked_chunks:
        return "No sources available to synthesize an answer from."

    facts = [c["metadata"]["text"].rstrip(".") for c in ranked_chunks]
    sources = [c["metadata"]["title"] for c in ranked_chunks]

    if len(facts) == 1:
        return f"{facts[0]}. [{sources[0]}]"

    combined = "; and ".join(facts[:-1]) + f"; and finally, {facts[-1]}"
    source_list = ", ".join(sources)
    return f"Putting these together: {combined}. [Sources: {source_list}]"


def detect_contradiction(chunk_a, chunk_b, contradiction_pairs):
    """
    CONTRADICTION DETECTION: checks whether two chunks contain a known
    pair of conflicting claims. contradiction_pairs is a list of
    (phrase_a, phrase_b) tuples -- if chunk_a contains phrase_a and
    chunk_b contains phrase_b (or vice versa), they're flagged as
    contradicting. This is a simplified stand-in for a real system,
    which would need an LLM (or NLI model) to detect contradictions in
    open-ended text; the DECISION of what to do once a contradiction is
    found is the more important part to get right.
    """
    text_a = chunk_a["metadata"]["text"].lower()
    text_b = chunk_b["metadata"]["text"].lower()

    for phrase_a, phrase_b in contradiction_pairs:
        if (phrase_a in text_a and phrase_b in text_b) or (phrase_b in text_a and phrase_a in text_b):
            return True
    return False


def handle_contradiction(query, chunk_a, chunk_b):
    """
    Once a contradiction is detected, the honest response is to SURFACE
    it, not silently pick one side. Hiding a contradiction (by only
    using one source) can make a confidently wrong answer; presenting
    both lets the user judge which source to trust.
    """
    title_a = chunk_a["metadata"]["title"]
    title_b = chunk_b["metadata"]["title"]
    return (
        f'Regarding "{query}", sources disagree:\n'
        f'  - {title_a} says: "{chunk_a["metadata"]["text"]}"\n'
        f'  - {title_b} says: "{chunk_b["metadata"]["text"]}"\n'
        f"I can't resolve this conflict from the sources alone -- you may "
        f"want to check which source is more current or authoritative."
    )


def express_uncertainty(answer, confidence_score):
    """
    UNCERTAINTY EXPRESSION: prepends an honest hedge when confidence is
    low, instead of stating a possibly-wrong answer with full authority.
    A RAG system that always sounds equally confident is actively
    misleading users about how much to trust any given answer.
    """
    if confidence_score >= 0.7:
        return answer
    if confidence_score >= 0.4:
        return f"I'm not fully certain, but based on the available information: {answer}"
    return (
        f"I have low confidence in this answer, and you should verify it "
        f"independently: {answer}"
    )


def needs_clarification(query, ranked_chunks, ambiguity_threshold=0.15):
    """
    FOLLOW-UP QUESTIONS: if the top-ranked chunks are all close in score
    to each other (no clear winner), that's often a sign the query
    itself was ambiguous -- it could reasonably mean several different
    things, and retrieval/ranking can't tell which one the user meant.
    Rather than guessing, it's better to ask.
    """
    if len(ranked_chunks) < 2:
        return False, None

    top_score = ranked_chunks[0].get("final_score", ranked_chunks[0].get("similarity", 0))
    second_score = ranked_chunks[1].get("final_score", ranked_chunks[1].get("similarity", 0))

    if (top_score - second_score) < ambiguity_threshold:
        topics = [c["metadata"]["title"] for c in ranked_chunks[:2]]
        clarifying_question = (
            f'Your question could relate to a few different things: '
            f'{" or ".join(topics)}. Could you clarify which one you mean?'
        )
        return True, clarifying_question

    return False, None


def structured_comparison(items):
    """
    STRUCTURED RESPONSES: renders a comparison as a Markdown table
    instead of prose. When a user is comparing multiple things
    (documents, options, tools), a table is far easier to scan than the
    same information buried in paragraph form.

    items: list of dicts, all sharing the same keys.
    """
    if not items:
        return "No items to compare."

    headers = list(items[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(str(item[h]) for h in headers) + " |"
        for item in items
    ]
    return "\n".join([header_row, separator_row] + data_rows)


def main():
    print("=== Advanced Generation Techniques ===\n")

    # --- 1. Multi-document synthesis ---
    print("--- 1. Multi-document synthesis ---")
    ranked_chunks = [
        {"metadata": {"title": "What is RAG", "text": "RAG retrieves relevant documents before generating an answer"}},
        {"metadata": {"title": "Why RAG Matters", "text": "RAG helps overcome outdated model knowledge"}},
    ]
    print(multi_document_synthesis("What is RAG?", ranked_chunks))
    print()

    # --- 2. Contradiction handling ---
    print("--- 2. Contradiction handling ---")
    chunk_a = {"metadata": {"title": "Pricing Page (old)", "text": "The premium plan costs $10 per month."}}
    chunk_b = {"metadata": {"title": "Pricing Page (new)", "text": "The premium plan costs $15 per month."}}
    contradiction_pairs = [("$10 per month", "$15 per month")]
    if detect_contradiction(chunk_a, chunk_b, contradiction_pairs):
        print(handle_contradiction("How much does the premium plan cost?", chunk_a, chunk_b))
    print()

    # --- 3. Uncertainty expression ---
    print("--- 3. Uncertainty expression ---")
    answer = "The premium plan likely costs around $10-15 per month."
    for confidence in [0.9, 0.5, 0.2]:
        print(f"  confidence={confidence}: {express_uncertainty(answer, confidence)}")
    print()

    # --- 4. Follow-up questions for ambiguous queries ---
    print("--- 4. Follow-up questions ---")
    ambiguous_results = [
        {"metadata": {"title": "Python (the language)"}, "final_score": 0.62},
        {"metadata": {"title": "Python (the snake species)"}, "final_score": 0.60},
    ]
    needs_clarify, question = needs_clarification("Tell me about Python", ambiguous_results)
    print(f"  Needs clarification: {needs_clarify}")
    if needs_clarify:
        print(f"  Follow-up: {question}")
    print()

    # --- 5. Structured comparison table ---
    print("--- 5. Structured comparison ---")
    items = [
        {"Database": "Pinecone", "Hosting": "Managed", "Best for": "Fast setup"},
        {"Database": "Milvus", "Hosting": "Self-hosted", "Best for": "Massive scale"},
        {"Database": "Chroma", "Hosting": "Local", "Best for": "Prototyping"},
    ]
    print(structured_comparison(items))

    print(
        "\nWhat makes these 'intelligent': each one is a response to a "
        "situation where a naive generator would either produce a "
        "misleadingly confident answer (ignoring contradictions or "
        "ambiguity) or a poorly-organized one (paragraphs instead of a "
        "table for a comparison). Recognizing WHEN to apply each "
        "technique is as important as the technique itself."
    )


if __name__ == "__main__":
    main()
