"""
chunking_strategies.py

Five ways to split a document into smaller pieces ("chunks"), each with a
different tradeoff between simplicity and quality. All of these work with
just plain Python -- no external libraries.
"""

import re


SAMPLE_DOCUMENT = """
Retrieval-Augmented Generation, or RAG, is a technique that combines search with
text generation. Instead of relying only on what a language model memorized during
training, a RAG system looks up relevant information first, then uses that
information to generate an answer.

This matters because language models have two big limitations. First, their
knowledge has a cutoff date, so they don't know about anything that happened after
they were trained. Second, they don't have access to private data, like a company's
internal documents, unless that data is explicitly given to them.

A typical RAG pipeline has three steps. First, documents are split into chunks and
turned into embeddings. Second, when a question comes in, the system searches for
the most relevant chunks using those embeddings. Third, the relevant chunks are
handed to a language model, along with the original question, to generate a final
answer.

Chunking is often the most overlooked part of this pipeline, but it has a big impact
on the quality of the final answer. If chunks are too big, they contain too much
irrelevant information, which can confuse the retrieval step. If chunks are too
small, they might not contain enough context to be useful on their own.
""".strip()


def chunk_by_fixed_size(text, chunk_size=200):
    """
    The simplest possible approach: cut the text every `chunk_size`
    characters, no matter what's there.

    Tradeoff: extremely simple and predictable chunk sizes, but it will
    happily cut a sentence (or even a word) right in half. Good for a
    quick prototype, bad for anything where chunk quality matters.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def chunk_by_tokens(text, tokens_per_chunk=40, overlap_tokens=0):
    """
    Splits by word count instead of character count ("tokens" here just
    means "words" -- real tokenizers are more complex, but word count is
    a good enough stand-in to see the idea). Optionally overlaps a few
    words between chunks so context isn't lost at the boundary.

    Tradeoff: more consistent chunk sizes in terms of actual content
    (some words are longer than others, but roughly evens out), but
    still doesn't respect sentence boundaries -- it can still cut a
    sentence in half, right between two words.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + tokens_per_chunk
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if overlap_tokens > 0:
            start = end - overlap_tokens
        else:
            start = end

    return chunks


def chunk_by_sentences(text, sentences_per_chunk=3):
    """
    Splits the text into sentences first, then groups a fixed number of
    sentences together per chunk. Never cuts a sentence in half.

    Tradeoff: respects sentence boundaries, which is a real improvement,
    but doesn't know or care whether those sentences are actually about
    the same topic -- it just groups them by count.
    """
    # A simple sentence splitter: break after ., !, or ?, followed by a
    # space. Not perfect (it would trip up on "Dr. Smith", for example),
    # but good enough for well-formed prose like ours.
    sentences = re.split(r'(?<=[.!?])\s+', text.replace("\n", " ").strip())
    sentences = [s for s in sentences if s]

    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)

    return chunks


def chunk_by_paragraphs(text):
    """
    Splits at paragraph breaks (blank lines). Each paragraph becomes its
    own chunk.

    Tradeoff: paragraphs are usually already a coherent idea, written
    that way by whoever wrote the document, so this often produces
    naturally good chunks with zero extra logic. The downside: paragraph
    length varies a lot, so chunk sizes can be wildly inconsistent, and
    a very long paragraph still ends up as one (possibly too-big) chunk.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def chunk_with_overlap(text, chunk_size=200, overlap=50):
    """
    Same as fixed-size chunking, but each chunk shares `overlap`
    characters with the chunk before it. If an idea spans a chunk
    boundary, the overlap means at least some of it appears in both
    neighboring chunks instead of being fully lost to one side.

    Tradeoff: helps preserve context across chunk boundaries, at the
    cost of some duplicated text (and therefore slightly more storage
    and embedding cost) across your dataset.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += step

    return chunks


def print_chunks(title, chunks, max_preview=80):
    print(f"--- {title} ({len(chunks)} chunks) ---")
    for i, chunk in enumerate(chunks, start=1):
        preview = chunk.replace("\n", " ").strip()
        if len(preview) > max_preview:
            preview = preview[:max_preview] + "..."
        print(f"  Chunk {i}: {preview}")
    print()


def main():
    print("=== Chunking Strategies Demo ===\n")

    print_chunks("Fixed-size (200 chars)", chunk_by_fixed_size(SAMPLE_DOCUMENT, chunk_size=200))
    print_chunks("By tokens (40 words, no overlap)", chunk_by_tokens(SAMPLE_DOCUMENT, tokens_per_chunk=40))
    print_chunks("By tokens (40 words, 10-word overlap)", chunk_by_tokens(SAMPLE_DOCUMENT, tokens_per_chunk=40, overlap_tokens=10))
    print_chunks("By sentences (3 per chunk)", chunk_by_sentences(SAMPLE_DOCUMENT, sentences_per_chunk=3))
    print_chunks("By paragraphs", chunk_by_paragraphs(SAMPLE_DOCUMENT))
    print_chunks("Fixed-size with overlap (200 chars, 50 overlap)", chunk_with_overlap(SAMPLE_DOCUMENT, chunk_size=200, overlap=50))

    print(
        "Notice fixed-size chunking cuts words in half mid-chunk, while "
        "sentence and paragraph chunking always end on a clean boundary. "
        "That difference is exactly what chunking_comparison.py measures next."
    )


if __name__ == "__main__":
    main()
