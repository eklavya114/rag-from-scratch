"""
prompt_engineering.py

We're not calling a real LLM in this project (no API keys needed), but
the PROMPTS we'd send to one are exactly what determines whether
generation would actually be good. This file builds and shows those
prompts, so the technique is visible even without an API call.
"""


def build_context_block(ranked_chunks):
    """Same idea as simple_generator.py's structure_context()."""
    lines = []
    for i, chunk in enumerate(ranked_chunks, start=1):
        title = chunk["metadata"]["title"]
        text = chunk["metadata"]["text"]
        lines.append(f"[{i}] Source: {title}\n{text}")
    return "\n\n".join(lines)


def system_prompt():
    """
    SYSTEM PROMPT: defines the model's role and constraints before it
    sees the actual question. This is where you set the ground rules --
    "only use the provided context," "say when you don't know," "cite
    sources" -- once, so every answer follows them consistently instead
    of relying on the question itself to ask nicely.
    """
    return (
        "You are a helpful assistant that answers questions using ONLY the "
        "provided context. If the context doesn't contain enough "
        "information to answer confidently, say so clearly instead of "
        "guessing. Always cite which source number ([1], [2], etc.) "
        "supports each claim you make."
    )


def question_answering_prompt(query, context_block):
    """
    QUESTION-ANSWERING STYLE: the most common RAG prompt shape. Direct
    question in, direct answer expected out, grounded in the given
    context.
    """
    return (
        f"{system_prompt()}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )


def summarization_prompt(context_block):
    """
    SUMMARIZATION STYLE: instead of answering a specific question, the
    model is asked to condense several sources into one coherent
    overview. Useful when a user asks something broad, like "tell me
    about X," rather than a narrow factual question.
    """
    return (
        f"{system_prompt()}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Summarize the key points from the context above in 2-3 sentences. "
        f"Preserve the source citations for each point.\n\n"
        f"Summary:"
    )


def explanation_prompt(query, context_block):
    """
    EXPLANATION STYLE: asks the model to teach the concept, not just
    state a fact. Useful for "what is X" or "how does X work" questions,
    where a one-line answer would be technically correct but unhelpful.
    """
    return (
        f"{system_prompt()}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Explain this in a way a beginner could understand, using the "
        f"context above. Use a concrete example if the context provides one.\n\n"
        f"Explanation:"
    )


def few_shot_prompt(query, context_block, examples):
    """
    FEW-SHOT PROMPTING: shows the model 1-2 examples of what a GOOD
    answer looks like before asking it to answer the real question. This
    matters because "good" is subjective -- few-shot examples make the
    expected tone, length, and citation style concrete instead of
    abstract, which produces much more consistent output than
    instructions alone.
    """
    examples_block = "\n\n".join(
        f"Example question: {ex['question']}\nExample answer: {ex['answer']}"
        for ex in examples
    )
    return (
        f"{system_prompt()}\n\n"
        f"Here are examples of well-formed answers:\n\n{examples_block}\n\n"
        f"Now answer this question the same way.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )


def chain_of_thought_prompt(query, context_block):
    """
    CHAIN-OF-THOUGHT PROMPTING: explicitly asks the model to reason
    through the context step by step BEFORE giving a final answer. This
    tends to catch cases where the naive first-glance answer is wrong --
    forcing the model to check each source against the question first
    surfaces contradictions or gaps it might otherwise skip past.
    """
    return (
        f"{system_prompt()}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"First, think step by step: for each source, note whether it is "
        f"relevant to the question and what it contributes. Then, using "
        f"only relevant sources, write a final answer.\n\n"
        f"Reasoning:"
    )


# A small library of prompt templates keyed by query type, so a real
# system could route a query to the right style automatically instead
# of always using one prompt shape for every kind of question.
PROMPT_TEMPLATES = {
    "factual": question_answering_prompt,
    "broad_overview": lambda query, context: summarization_prompt(context),
    "conceptual": explanation_prompt,
}


def main():
    print("=== Prompt Engineering Demo ===\n")

    ranked_chunks = [
        {
            "metadata": {
                "title": "What is RAG",
                "text": "RAG stands for Retrieval-Augmented Generation. It retrieves "
                        "relevant documents before generating an answer.",
            },
        },
        {
            "metadata": {
                "title": "Why RAG Matters",
                "text": "RAG matters because language models can be outdated. Retrieval "
                        "lets them use fresh information without retraining.",
            },
        },
    ]
    context_block = build_context_block(ranked_chunks)
    query = "What is RAG and why does it matter?"

    print("--- 1. Question-answering prompt ---")
    print(question_answering_prompt(query, context_block))
    print()

    print("--- 2. Summarization prompt ---")
    print(summarization_prompt(context_block))
    print()

    print("--- 3. Explanation prompt ---")
    print(explanation_prompt(query, context_block))
    print()

    print("--- 4. Few-shot prompt ---")
    examples = [
        {
            "question": "What is a vector database?",
            "answer": "A vector database stores embeddings and finds the closest "
                      "matches to a query quickly [1]. It's what makes fast semantic "
                      "search possible at scale.",
        }
    ]
    print(few_shot_prompt(query, context_block, examples))
    print()

    print("--- 5. Chain-of-thought prompt ---")
    print(chain_of_thought_prompt(query, context_block))
    print()

    print("--- 6. Routing by query type ---")
    # Lambdas all report the same generic "__name__" ('<lambda>'), so we
    # label those by hand instead of relying on introspection to give a
    # meaningful name.
    friendly_names = {"broad_overview": "summarization_prompt (wrapped)"}
    for query_type, template_fn in PROMPT_TEMPLATES.items():
        name = friendly_names.get(query_type, template_fn.__name__)
        print(f"  query_type='{query_type}' -> uses {name}")

    print(
        "\nWhy this matters: the SAME context and question can produce very "
        "different quality answers depending on how the prompt is written. "
        "A vague prompt ('answer the question') leaves too much to chance. "
        "A well-structured prompt tells the model exactly what role to "
        "play, what data it's allowed to use, how to cite it, and -- with "
        "few-shot and chain-of-thought -- what GOOD actually looks like."
    )


if __name__ == "__main__":
    main()
