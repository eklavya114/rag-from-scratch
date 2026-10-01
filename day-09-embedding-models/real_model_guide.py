"""
real_model_guide.py

This file is different from the others in this folder: it's not meant to
be run. It won't connect to anything, and there are no API keys here.

Instead, this shows what the CODE looks like for four real embedding
models/providers, so you can compare approaches and see what switching
between them would actually involve, without needing an API key to read
it. Same idea as Day 3's real_vector_dbs.py.
"""


def openai_small_example():
    """
    OpenAI text-embedding-3-small: fast, cheap, solid general-purpose
    quality. A common default for getting started or for high-volume
    workloads where cost matters more than squeezing out the last bit
    of retrieval quality.

    Pricing (approximate, check OpenAI's current pricing): very low
    cost per token, among the cheapest hosted options available.
    """
    example_code = '''
    from openai import OpenAI

    client = OpenAI(api_key="YOUR_API_KEY")  # keep this in an environment variable

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="RAG retrieves relevant documents before generating an answer.",
    )
    embedding = response.data[0].embedding  # a list of 1536 floats
    '''
    print("--- OpenAI text-embedding-3-small ---")
    print("Use when: cost and speed matter most, general-purpose quality is enough.")
    print(example_code)


def openai_large_example():
    """
    OpenAI text-embedding-3-large: the same provider, a bigger model.
    Higher quality (particularly on harder/more nuanced queries), at
    higher cost and somewhat higher latency per call.
    """
    example_code = '''
    from openai import OpenAI

    client = OpenAI(api_key="YOUR_API_KEY")

    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="RAG retrieves relevant documents before generating an answer.",
    )
    embedding = response.data[0].embedding  # a list of 3072 floats

    # Note: both OpenAI embedding models support a `dimensions` parameter
    # to request a SHORTER embedding than the default, trading a little
    # quality for less storage and faster similarity search.
    response_shortened = client.embeddings.create(
        model="text-embedding-3-large",
        input="RAG retrieves relevant documents before generating an answer.",
        dimensions=1024,
    )
    '''
    print("--- OpenAI text-embedding-3-large ---")
    print("Use when: retrieval quality is a measured bottleneck and the extra cost is justified.")
    print(example_code)


def mistral_embed_example():
    """
    Mistral Embed: a capable alternative embedding API, useful when you
    want a different vendor relationship, pricing structure, or data
    handling policy than OpenAI's.
    """
    example_code = '''
    from mistralai import Mistral

    client = Mistral(api_key="YOUR_API_KEY")

    response = client.embeddings.create(
        model="mistral-embed",
        inputs=["RAG retrieves relevant documents before generating an answer."],
    )
    embedding = response.data[0].embedding
    '''
    print("--- Mistral Embed ---")
    print("Use when: you want an alternative to OpenAI for pricing, vendor diversity, or data policy reasons.")
    print(example_code)


def sentence_transformers_example():
    """
    Sentence-Transformers: open source, runs locally, no API calls or
    per-token cost at all once downloaded. The right choice when privacy
    matters (nothing leaves your machine), when you need to run fully
    offline, or when API cost at your volume would be prohibitive.
    """
    example_code = '''
    from sentence_transformers import SentenceTransformer

    # Downloaded once, then runs entirely on your own hardware (CPU or GPU).
    model = SentenceTransformer("all-MiniLM-L6-v2")

    embedding = model.encode("RAG retrieves relevant documents before generating an answer.")
    # embedding is a numpy array, 384 dimensions for this particular model

    # Batch encoding is much faster per-item than one-at-a-time calls.
    embeddings = model.encode([
        "First document chunk.",
        "Second document chunk.",
        "Third document chunk.",
    ])
    '''
    print("--- Sentence-Transformers (local) ---")
    print("Use when: privacy/offline requirements matter, or API cost at your volume is prohibitive.")
    print(example_code)


def quick_comparison_table():
    print("--- Quick comparison ---\n")
    rows = [
        ("Model", "Hosting", "Relative cost", "Relative quality", "Best for"),
        ("text-embedding-3-small", "API (OpenAI)", "Very low", "Good", "Default starting point"),
        ("text-embedding-3-large", "API (OpenAI)", "Moderate", "Very good", "Quality-critical retrieval"),
        ("Mistral Embed", "API (Mistral)", "Low-moderate", "Good", "Vendor diversity"),
        ("Sentence-Transformers", "Local/self-hosted", "Compute only", "Good (model-dependent)", "Privacy, offline, high volume"),
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  " + " | ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def main():
    print("=== Real Embedding Model Guide ===")
    print("(Code structure only -- nothing here actually runs or connects to anything.\n"
          " No API key needed to read it.)\n")

    openai_small_example()
    openai_large_example()
    mistral_embed_example()
    sentence_transformers_example()
    quick_comparison_table()


if __name__ == "__main__":
    main()
