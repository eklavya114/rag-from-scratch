"""
simple_generator.py

The simplest possible generation systems: no LLM API, just plain Python
string handling. Two approaches:

  1. Template-based: fill a fixed sentence structure with retrieved info.
  2. Concatenation-based: stitch the retrieved chunks together, with
     light formatting and citations.

Both take the same input shape as Day 6's ranked results: a list of
dicts with "metadata" (including "title" and "text") and a similarity
or final_score.
"""


class Generator:
    """
    Turns a ranked list of chunks into a readable answer, using either a
    template or a concatenation strategy.
    """

    def generate_template(self, query, ranked_chunks):
        """
        TEMPLATE-BASED GENERATION.

        Fills a fixed sentence structure using the single best-ranked
        chunk. Predictable and safe -- it can never invent anything,
        since it's just plugging text into a fixed shape -- but it can
        only ever produce one specific kind of sentence, regardless of
        what was actually asked.
        """
        if not ranked_chunks:
            return "I don't have any relevant information to answer that question."

        best_chunk = ranked_chunks[0]
        title = best_chunk["metadata"]["title"]
        text = best_chunk["metadata"]["text"]

        return f'Based on "{title}": {text}'

    def generate_concatenation(self, query, ranked_chunks, max_chunks=3):
        """
        CONCATENATION-BASED GENERATION.

        Stitches together the top few ranked chunks, each labeled with
        its source. Nothing is invented or summarized -- this is
        completely faithful to the sources, but it reads as a list of
        excerpts rather than one coherent answer. That's the honest
        tradeoff: zero risk of fabrication, at the cost of zero real
        synthesis.
        """
        if not ranked_chunks:
            return "I don't have any relevant information to answer that question."

        top_chunks = ranked_chunks[:max_chunks]
        parts = [f"Regarding \"{query}\", here's what I found:"]

        for i, chunk in enumerate(top_chunks, start=1):
            title = chunk["metadata"]["title"]
            text = chunk["metadata"]["text"]
            parts.append(f"{i}. From \"{title}\": {text}")

        return "\n\n".join(parts)

    def format_answer(self, answer_text, sources):
        """
        Wraps a generated answer with a clear, consistent source list at
        the end. Keeping this as a separate step means both generation
        strategies above (and future ones) can share the exact same
        citation formatting, instead of each reinventing it slightly
        differently.
        """
        if not sources:
            return answer_text

        source_lines = "\n".join(f"  - {s}" for s in sources)
        return f"{answer_text}\n\nSources:\n{source_lines}"

    def structure_context(self, ranked_chunks):
        """
        Turns a list of ranked chunks into a single "context block" --
        the shape a real LLM prompt would actually receive. Shown here
        so the structure is visible even without an LLM call: numbered
        excerpts, each labeled with its source title, ready to be
        inserted into a prompt template (see prompt_engineering.py).
        """
        lines = []
        for i, chunk in enumerate(ranked_chunks, start=1):
            title = chunk["metadata"]["title"]
            text = chunk["metadata"]["text"]
            lines.append(f"[{i}] Source: {title}\n{text}")
        return "\n\n".join(lines)


def main():
    print("=== Simple Generation Demo ===\n")

    # A small set of already-ranked chunks, shaped exactly like Day 6's
    # PracticalRanker output, so this reads as "the next stage after
    # ranking" rather than a disconnected new example.
    ranked_chunks = [
        {
            "metadata": {
                "title": "What is RAG",
                "text": "RAG stands for Retrieval-Augmented Generation. It retrieves "
                        "relevant documents before generating an answer.",
            },
            "final_score": 0.92,
        },
        {
            "metadata": {
                "title": "Why RAG Matters",
                "text": "RAG matters because language models can be outdated. Retrieval "
                        "lets them use fresh information without retraining.",
            },
            "final_score": 0.78,
        },
    ]

    query = "What is RAG and why does it matter?"
    generator = Generator()

    print(f"Query: \"{query}\"\n")

    print("--- Context structured for a prompt ---")
    print(generator.structure_context(ranked_chunks))
    print()

    print("--- Template-based answer ---")
    template_answer = generator.generate_template(query, ranked_chunks)
    sources = [c["metadata"]["title"] for c in ranked_chunks[:1]]
    print(generator.format_answer(template_answer, sources))
    print()

    print("--- Concatenation-based answer ---")
    concat_answer = generator.generate_concatenation(query, ranked_chunks)
    sources = [c["metadata"]["title"] for c in ranked_chunks]
    print(generator.format_answer(concat_answer, sources))
    print()

    print("--- No relevant chunks (edge case) ---")
    print(generator.generate_template(query, []))

    print(
        "\nNotice the template answer only ever uses the SINGLE top chunk -- "
        "it can't combine 'What is RAG' and 'Why RAG Matters' into one "
        "answer, even though both are relevant. The concatenation answer "
        "uses both, but reads as two separate excerpts rather than one "
        "synthesized explanation. Neither approach can truly weave the two "
        "ideas together the way a real LLM-based generator could -- that's "
        "exactly the gap prompt_engineering.py exists to set up for."
    )


if __name__ == "__main__":
    main()
