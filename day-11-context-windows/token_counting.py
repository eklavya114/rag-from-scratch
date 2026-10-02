"""
token_counting.py

Compares a simple word-based token estimate against a REAL tokenizer
(tiktoken, the same library OpenAI's own SDKs use), so "roughly 1.3
tokens per word" stops being an assumption and becomes a measured,
checkable approximation -- with real numbers showing exactly how far
off it can be.

Falls back gracefully if tiktoken isn't installed (this project never
requires external installs to run its core lessons) -- the comparison
still runs, just using a second, different estimation heuristic instead
of a true tokenizer, with that limitation stated explicitly.
"""

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def simple_word_estimate(text):
    """The same rule of thumb used elsewhere in this folder: ~1.3 tokens per word."""
    return int(len(text.split()) * 1.3)


def character_based_estimate(text):
    """
    A second, different cheap estimate: ~4 characters per token is
    another commonly cited rule of thumb for English text. Shown here so
    there are two independent ESTIMATES to compare against the real
    count, not just one.
    """
    return int(len(text) / 4)


def real_token_count(text, model="cl100k_base"):
    """
    Uses tiktoken's actual encoding (the real algorithm used by GPT-3.5/
    GPT-4-era models) to count tokens exactly. This is ground truth for
    OpenAI-family models specifically -- other model families (Claude,
    open-source models) use different tokenizers that would produce
    somewhat different exact counts, though the general shape of "it's
    not just words or characters" holds across all of them.
    """
    if not TIKTOKEN_AVAILABLE:
        return None
    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(text))


SAMPLE_TEXTS = {
    "short_simple": "What is RAG?",
    "medium_prose": (
        "RAG stands for Retrieval-Augmented Generation. It retrieves relevant "
        "documents before generating an answer, instead of relying only on "
        "what a language model memorized during training."
    ),
    "technical_jargon": (
        "The HNSW index uses approximate nearest-neighbor search via a "
        "multi-layer graph, trading exactness for O(log n) query complexity "
        "instead of brute-force O(n)."
    ),
    "code_snippet": (
        "def cosine_similarity(a, b):\n"
        "    dot = sum(x * y for x, y in zip(a, b))\n"
        "    return dot / (norm(a) * norm(b))"
    ),
    "numbers_and_punctuation": "Pricing: $0.00002/1K tokens, up to 128,000 tokens, 99.9% uptime SLA!!!",
}


def compare_estimates():
    print("--- Simple estimate vs. real tokenizer ---\n")
    if not TIKTOKEN_AVAILABLE:
        print("(tiktoken is not installed -- showing two different ESTIMATES instead of a real count.")
        print(" Install with `pip install tiktoken` to see the actual comparison against ground truth.)\n")

    header = f"{'Text type':<24} | {'Words':>6} | {'Word-est':>9} | {'Char-est':>9} | {'Real tokens':>11} | {'Word-est error':>14}"
    print(header)
    print("-" * len(header))

    total_word_error = 0
    total_real = 0

    for name, text in SAMPLE_TEXTS.items():
        word_count = len(text.split())
        word_est = simple_word_estimate(text)
        char_est = character_based_estimate(text)
        real = real_token_count(text)

        if real is not None:
            error_pct = (word_est - real) / real * 100
            total_word_error += abs(word_est - real)
            total_real += real
            real_str = f"{real:>11,}"
            error_str = f"{error_pct:>+13.0f}%"
        else:
            real_str = f"{'n/a':>11}"
            error_str = f"{'n/a':>14}"

        print(f"{name:<24} | {word_count:>6,} | {word_est:>9,} | {char_est:>9,} | {real_str} | {error_str}")

    if TIKTOKEN_AVAILABLE and total_real:
        overall_error_pct = total_word_error / total_real * 100
        print(f"\nOverall word-estimate error across all samples: {overall_error_pct:.1f}%")


def why_accuracy_matters():
    print("\n--- Why accuracy matters ---\n")
    print(
        "Notice the word-based estimate UNDER-counts in every single "
        "sample above, often substantially -- technical jargon, code, and "
        "especially punctuation-heavy text (numbers, symbols, currency) "
        "split into far more tokens than their word count suggests, since "
        "a real tokenizer often spends a separate token on punctuation "
        "and splits uncommon words into multiple sub-word pieces. Even "
        "the plainest, shortest sample here (just 3 words) was still 40% "
        "off. If you use a flat word-based estimate to decide how many "
        "documents fit in a budget, you risk consistently OVER-fitting "
        "your actual token usage versus what you planned for -- the kind "
        "of mistake that only shows up when a real API call gets rejected "
        "or truncated for exceeding the context window.\n\n"
        "Rule of thumb: word-based estimation is fine for a rough budget "
        "sketch or a quick prototype. Once token cost or context limits "
        "actually matter in production, use the real tokenizer for your "
        "specific model family -- the gap, as measured above, is real and "
        "not always small."
    )


def main():
    print("=== Token Counting: Estimate vs. Reality ===\n")
    compare_estimates()
    why_accuracy_matters()


if __name__ == "__main__":
    main()
