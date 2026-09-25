"""
real_world_examples.py

Chunking strategy isn't one-size-fits-all. The right approach depends on
what kind of document you're chunking. This file walks through five
common document types, shows a chunking approach suited to each, and
explains why that approach fits.
"""

from chunking_strategies import chunk_by_paragraphs, chunk_by_sentences


def technical_documentation_example():
    """
    Technical docs (API references, code documentation) are usually
    already organized around functions, classes, or sections. The best
    strategy: chunk by these natural units (one function's docs = one
    chunk), never splitting a code block from its explanation.
    """
    doc = """
def cosine_similarity(a, b):
    \"\"\"Returns how similar two vectors are, from -1 to 1.\"\"\"
    ...

This function measures similarity between two embeddings. A result close
to 1 means the vectors point in nearly the same direction. A result close
to 0 means they're unrelated.

def chunk_by_sentences(text, sentences_per_chunk=3):
    \"\"\"Splits text into groups of sentences.\"\"\"
    ...

This function splits text at sentence boundaries, then groups a fixed
number of sentences per chunk, avoiding broken sentences.
""".strip()

    # Split on the natural "def " boundaries -- each function plus its
    # explanation becomes one chunk. This is a simplified stand-in for
    # what a real code-aware chunker (like one that parses an AST) would
    # do automatically.
    chunks = ["def " + part.strip() for part in doc.split("def ") if part.strip()]

    print("--- Technical Documentation ---")
    print("Best strategy: chunk by function/section, keep code with its explanation.\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {chunk[:70].strip()}...")
    print(
        "\n  Why: separating a function signature from its explanation (or "
        "splitting mid-code-block) makes both halves useless on their own. "
        "Chunking by function/section keeps each piece self-contained.\n"
    )


def news_article_example():
    """
    News articles are written with an inverted pyramid structure: the
    most important information comes first, details follow in later
    paragraphs. Paragraph-based chunking works well here because each
    paragraph is usually a self-contained fact or development.
    """
    article = """
A new study released Tuesday found that regular exercise significantly
reduces the risk of several chronic diseases. Researchers tracked 10,000
participants over five years.

The study, published in a leading medical journal, showed a 30% reduction
in heart disease risk among participants who exercised at least three
times per week.

Experts say the findings reinforce existing guidelines recommending at
least 150 minutes of moderate exercise per week for adults.
""".strip()

    chunks = chunk_by_paragraphs(article)

    print("--- News Article ---")
    print("Best strategy: paragraph-based chunking.\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {chunk[:70]}...")
    print(
        "\n  Why: each paragraph typically covers one fact or development. "
        "Paragraph boundaries already do the hard work of separating ideas "
        "for you -- no extra logic needed.\n"
    )


def legal_document_example():
    """
    Legal documents are organized into numbered clauses or sections, and
    each one usually needs to be understood as a complete, self-contained
    unit -- splitting a clause in half can change its legal meaning
    entirely. The best strategy: chunk by clause/section number, never by
    a fixed character or word count.
    """
    contract = """
1. Definitions. "Agreement" means this document and all attached
exhibits. "Effective Date" means the date both parties sign this
Agreement.

2. Term. This Agreement begins on the Effective Date and continues for
twelve (12) months, unless terminated earlier under Section 5.

3. Payment. Client agrees to pay Provider within thirty (30) days of
receiving an invoice. Late payments accrue interest at 1.5% per month.
""".strip()

    # Split on numbered clause markers like "1.", "2.", "3." at the start
    # of a line -- a simplified stand-in for a real legal-document parser.
    import re
    parts = re.split(r'\n(?=\d+\.\s)', contract)
    chunks = [p.strip() for p in parts if p.strip()]

    print("--- Legal Document ---")
    print("Best strategy: chunk by clause/section, never split mid-clause.\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {chunk[:70]}...")
    print(
        "\n  Why: legal meaning depends on complete clauses. Splitting "
        "Section 2 in half could separate the term length from the "
        "condition that cancels it early -- a serious, meaning-changing "
        "mistake in a legal context.\n"
    )


def research_paper_example():
    """
    Research papers have a well-known structure: abstract, introduction,
    methods, results, conclusion. Chunking by these named sections keeps
    each chunk focused on one purpose (e.g. a chunk from "Methods" won't
    accidentally include unrelated "Results" text).
    """
    paper = """
Abstract: This paper presents a new method for chunking documents based
on semantic similarity rather than fixed size.

Introduction: Prior work on retrieval-augmented generation has largely
treated chunking as a fixed-size problem, overlooking semantic coherence.

Methods: We measure sentence-level similarity using embeddings and group
sentences into chunks when their similarity exceeds a threshold.

Results: Semantic chunking produced chunks that were rated as more
coherent by human reviewers, compared to fixed-size chunking.
""".strip()

    # Split on the named section headers.
    import re
    parts = re.split(r'\n(?=[A-Z][a-z]+:)', paper)
    chunks = [p.strip() for p in parts if p.strip()]

    print("--- Research Paper ---")
    print("Best strategy: chunk by named section (Abstract, Methods, Results, etc).\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {chunk[:70]}...")
    print(
        "\n  Why: someone searching for 'what method did they use' should "
        "retrieve the Methods section, not a chunk that mixes Methods and "
        "Results together just because of where a word count happened to "
        "land.\n"
    )


def customer_support_example():
    """
    Support docs are often already structured as question-and-answer
    pairs. The best strategy: keep each Q&A pair as exactly one chunk.
    Splitting a question from its answer (or grouping multiple unrelated
    Q&As into one chunk) actively hurts retrieval.
    """
    faq = """
Q: How do I reset my password?
A: Go to Settings > Account > Reset Password, and follow the emailed link.

Q: How do I cancel my subscription?
A: Go to Settings > Billing > Cancel Subscription. Your access continues
until the end of the current billing period.

Q: Can I get a refund?
A: Refunds are available within 14 days of purchase. Contact support with
your order number to request one.
""".strip()

    # Split on each "Q:" marker -- one question+answer pair per chunk.
    import re
    parts = re.split(r'\n(?=Q:)', faq)
    chunks = [p.strip() for p in parts if p.strip()]

    print("--- Customer Support Docs ---")
    print("Best strategy: one Q&A pair per chunk.\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}: {chunk[:70]}...")
    print(
        "\n  Why: a retrieved chunk with a question but no answer (or an "
        "answer with no question) is far less useful to an LLM trying to "
        "respond helpfully. Keeping pairs intact keeps chunks self-contained.\n"
    )


def main():
    print("=== Chunking Strategy by Document Type ===\n")
    technical_documentation_example()
    news_article_example()
    legal_document_example()
    research_paper_example()
    customer_support_example()

    print("=" * 60)
    print(
        "\nBig takeaway: the best chunk boundary is almost always the "
        "boundary the document ALREADY has -- a function, a paragraph, a "
        "clause, a section, a Q&A pair. Generic strategies (fixed-size, "
        "sentence-count) are a reasonable fallback when a document doesn't "
        "have clear structure, but a structure-aware approach almost always "
        "produces better chunks when the structure is there to use."
    )


if __name__ == "__main__":
    main()
