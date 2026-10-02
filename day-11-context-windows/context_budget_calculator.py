"""
context_budget_calculator.py

Works out exactly how much of a model's context window is actually
available for documents, once the system prompt, the user's query, the
conversation so far, and room for the model's response are all
accounted for.
"""


def estimate_tokens(text):
    """
    A simple word-based token estimate: ~1.3 tokens per word is a
    commonly used rule of thumb for English text (real tokenizers split
    some words into multiple tokens, and some punctuation/whitespace
    into their own tokens too). See token_counting.py for how this
    compares against a real tokenizer.
    """
    return int(len(text.split()) * 1.3)


class ContextBudget:
    """
    Computes how many tokens are left for retrieved documents, given a
    model's total context window and everything else that has to share
    it.
    """

    def __init__(self, model_context_window, reserved_response_tokens):
        self.model_context_window = model_context_window
        self.reserved_response_tokens = reserved_response_tokens

    def calculate(self, system_prompt, query, conversation_history=""):
        """
        Returns a full budget breakdown: what's used by each fixed
        component, and what's left over for documents.
        """
        system_tokens = estimate_tokens(system_prompt)
        query_tokens = estimate_tokens(query)
        history_tokens = estimate_tokens(conversation_history) if conversation_history else 0

        fixed_cost = system_tokens + query_tokens + history_tokens + self.reserved_response_tokens
        remaining_for_documents = max(0, self.model_context_window - fixed_cost)

        return {
            "model_context_window": self.model_context_window,
            "system_prompt_tokens": system_tokens,
            "query_tokens": query_tokens,
            "history_tokens": history_tokens,
            "reserved_response_tokens": self.reserved_response_tokens,
            "fixed_cost": fixed_cost,
            "remaining_for_documents": remaining_for_documents,
        }


def cost_per_document(documents):
    """Shows the token cost of each candidate document individually, so you can see what you're spending budget on."""
    return [(doc["title"], estimate_tokens(doc["text"])) for doc in documents]


def predict_how_many_fit(documents, remaining_budget):
    """
    Walks down a list of documents (assumed already sorted best-first --
    see document_selection_strategies.py for how that order gets
    decided) and predicts how many actually fit within the remaining
    token budget, stopping as soon as the next one wouldn't.
    """
    fitted = []
    total_tokens = 0
    for doc in documents:
        doc_tokens = estimate_tokens(doc["text"])
        if total_tokens + doc_tokens > remaining_budget:
            break
        fitted.append(doc)
        total_tokens += doc_tokens
    return fitted, total_tokens


def print_budget_breakdown(breakdown):
    print(f"Model context window:        {breakdown['model_context_window']:>6,} tokens")
    print(f"  System prompt:              {breakdown['system_prompt_tokens']:>6,} tokens")
    print(f"  Query:                      {breakdown['query_tokens']:>6,} tokens")
    print(f"  Conversation history:       {breakdown['history_tokens']:>6,} tokens")
    print(f"  Reserved for response:      {breakdown['reserved_response_tokens']:>6,} tokens")
    print(f"  Fixed cost (total):         {breakdown['fixed_cost']:>6,} tokens")
    print(f"Remaining for documents:     {breakdown['remaining_for_documents']:>6,} tokens")


def main():
    print("=== Context Budget Calculator ===\n")

    system_prompt = (
        "You are a helpful assistant that answers questions using ONLY the "
        "provided context. If the context doesn't contain enough information, "
        "say so clearly. Always cite which source supports each claim you make."
    )
    query = "What is RAG and why does it matter for keeping answers up to date?"

    budget = ContextBudget(model_context_window=4096, reserved_response_tokens=500)
    breakdown = budget.calculate(system_prompt, query)

    print("--- Scenario: a 4,096-token context window (an older/smaller model) ---\n")
    print_budget_breakdown(breakdown)
    print()

    # Sized so the SMALL (4,096-token) scenario genuinely can't fit all
    # four -- forcing a real selection decision, which is the whole point
    # of this comparison. The LARGE (128,000-token) scenario easily fits
    # all of them regardless.
    documents = [
        {"title": "What is RAG", "text": "RAG stands for Retrieval-Augmented Generation. " * 150},
        {"title": "Why RAG Matters", "text": "RAG matters because language models can be outdated. " * 200},
        {"title": "What is a Vector Database", "text": "A vector database stores embeddings for fast search. " * 250},
        {"title": "Keyword Search Basics", "text": "Keyword search finds exact matching words. " * 100},
    ]

    print("--- Document costs ---\n")
    for title, tokens in cost_per_document(documents):
        print(f"  {title:<28}: ~{tokens:,} tokens")

    fitted, used_tokens = predict_how_many_fit(documents, breakdown["remaining_for_documents"])
    print(f"\n{len(fitted)} of {len(documents)} documents fit in the {breakdown['remaining_for_documents']:,}-token "
          f"document budget (using {used_tokens:,} tokens):")
    for doc in fitted:
        print(f"  - {doc['title']}")

    print("\n--- Scenario: a 128,000-token context window (a modern large-context model) ---\n")
    large_budget = ContextBudget(model_context_window=128_000, reserved_response_tokens=2000)
    large_breakdown = large_budget.calculate(system_prompt, query)
    print_budget_breakdown(large_breakdown)
    fitted_large, used_large = predict_how_many_fit(documents, large_breakdown["remaining_for_documents"])
    print(f"\n{len(fitted_large)} of {len(documents)} documents fit (using {used_large:,} of "
          f"{large_breakdown['remaining_for_documents']:,} available tokens).")

    print(
        "\nNotice the smaller model's budget couldn't fit every document, "
        "forcing a real selection decision -- which is exactly what "
        "document_selection_strategies.py explores next. The larger "
        "model's budget fit everything easily, but that doesn't mean "
        "dumping in every retrieved document is actually the best "
        "choice -- see quality_analysis_by_context.py for why."
    )


if __name__ == "__main__":
    main()
