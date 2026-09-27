"""
answer_formatting.py

The same underlying answer can be presented in very different shapes,
depending on who's reading it and how. This file shows five formats for
the exact same answer content, so the difference is concrete.
"""

import json


def format_plain_text(answer, sources):
    """
    PLAIN TEXT WITH SOURCES: the simplest possible format. Good for a
    chat interface, a text message, or anywhere formatting markup
    wouldn't render.
    """
    source_list = ", ".join(sources)
    return f"{answer}\n\nSources: {source_list}"


def format_markdown(answer, sources, title="Answer"):
    """
    MARKDOWN FORMATTED: headers and lists make longer or more structured
    answers easier to scan. Good for a docs page, a README, or a chat UI
    that renders Markdown.
    """
    lines = [f"## {title}", "", answer, "", "### Sources"]
    for source in sources:
        lines.append(f"- {source}")
    return "\n".join(lines)


def format_structured_json(answer, sources, confidence):
    """
    STRUCTURED JSON: machine-readable, meant for another program to
    consume (an API response, a downstream UI component, a logging
    pipeline) rather than for a human to read directly.
    """
    return json.dumps({
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }, indent=2)


def format_with_explanation(answer, explanation, sources):
    """
    ANSWER + EXPLANATION + SOURCES: separates the direct answer from the
    reasoning behind it. Good when users want a quick answer but also
    the OPTION to see why, without forcing everyone to read the
    reasoning every time.
    """
    lines = [
        f"Answer: {answer}",
        "",
        f"Why: {explanation}",
        "",
        "Sources:",
    ]
    for source in sources:
        lines.append(f"  - {source}")
    return "\n".join(lines)


def format_with_confidence(answer, sources, confidence_score):
    """
    ANSWER WITH CONFIDENCE SCORE: makes uncertainty visible instead of
    presenting every answer with the same false authority. A low
    confidence score should change how much a user trusts (or
    double-checks) the answer.
    """
    if confidence_score >= 0.7:
        confidence_label = "High confidence"
    elif confidence_score >= 0.4:
        confidence_label = "Medium confidence"
    else:
        confidence_label = "Low confidence"

    source_list = ", ".join(sources)
    return (
        f"{answer}\n\n"
        f"[{confidence_label}: {confidence_score:.0%}]\n"
        f"Sources: {source_list}"
    )


def main():
    print("=== Answer Formatting Demo ===\n")

    answer = (
        "RAG (Retrieval-Augmented Generation) combines search with text "
        "generation: it retrieves relevant documents before generating an "
        "answer, which helps it stay accurate and up to date."
    )
    explanation = (
        "This combines information from two sources: one defining RAG, and "
        "one explaining why retrieval helps overcome a language model's "
        "training cutoff."
    )
    sources = ["What is RAG", "Why RAG Matters"]
    confidence = 0.85

    print("--- 1. Plain text ---")
    print(format_plain_text(answer, sources))
    print()

    print("--- 2. Markdown ---")
    print(format_markdown(answer, sources, title="What is RAG?"))
    print()

    print("--- 3. Structured JSON ---")
    print(format_structured_json(answer, sources, confidence))
    print()

    print("--- 4. Answer + explanation + sources ---")
    print(format_with_explanation(answer, explanation, sources))
    print()

    print("--- 5. Answer with confidence score ---")
    print(format_with_confidence(answer, sources, confidence))
    print()

    print("--- Low-confidence example ---")
    print(format_with_confidence(
        "Based on limited information, this may relate to retrieval systems.",
        ["Keyword Search Basics"],
        0.25,
    ))

    print(
        "\nWhen to use which:\n"
        "- Plain text: chat interfaces, SMS, anywhere without markup rendering.\n"
        "- Markdown: docs pages, README-style output, chat UIs that render it.\n"
        "- Structured JSON: APIs, another program consuming the answer.\n"
        "- Answer + explanation: users who want a quick answer with reasoning "
        "available on demand, not forced on every response.\n"
        "- Confidence score: anywhere a wrong answer would be costly enough "
        "that the user needs to know how much to trust it."
    )


if __name__ == "__main__":
    main()
