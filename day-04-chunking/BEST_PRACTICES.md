# Chunking Best Practices

A quick reference for chunking decisions once you're building a real RAG system,
beyond the toy examples in this folder.

## Picking a chunk size

There's no universal "correct" chunk size, but a few rules of thumb:

- **Too small** (a single sentence, or less): chunks lack enough context to be
  useful on their own, and you end up with a huge number of chunks to search
  through, most of which are barely distinguishable from each other.
- **Too large** (multiple pages): chunks cover too many topics at once, which
  makes the embedding a blurry average and makes it hard for retrieval to tell
  whether a chunk is *actually* relevant or just partially relevant.
- **A common starting point**: 200-500 words (or roughly 300-800 characters) per
  chunk, then adjust based on your specific documents and how retrieval performs.

## Always prefer structure-aware chunking when structure exists

If your document already has natural boundaries -- headers, paragraphs, code
blocks, Q&A pairs, numbered clauses -- use them. A generic fixed-size or
sentence-count splitter is a fallback for unstructured text, not a first choice
when better boundaries already exist (see `real_world_examples.py`).

## Use overlap, but don't overdo it

A small overlap (10-20% of chunk size) between consecutive chunks helps prevent
losing context right at a chunk boundary. Too much overlap wastes storage and
embedding cost on duplicated text without adding much benefit -- there's a
diminishing return past a certain point.

## Keep metadata with every chunk

Every chunk should carry metadata back to its source: which document it came from,
what section, maybe a URL or page number. When a chunk gets retrieved and shown to
an LLM (or a user), that context matters -- "this came from the Refunds section of
the FAQ" is much more useful than an anonymous floating paragraph.

## Test your chunking, don't just assume it's fine

Use metrics like the ones in `chunk_quality.py` (completeness ratio, context loss
score) to actually measure your chunking output, especially after changing chunk
size or switching strategies. It's easy to assume a chunking approach "should" work
and be wrong -- test it against real documents from your own use case.

## When to reach for semantic chunking

Semantic chunking (grouping by topic similarity, not mechanical rules) is more
expensive to run, since it needs an embedding per sentence just to decide chunk
boundaries. It's worth it when:

- Your documents don't have clean structural boundaries (long-form prose, transcripts).
- Retrieval quality matters enough to justify the extra preprocessing cost.

It's probably overkill when your documents already have strong natural structure
(FAQs, well-formatted docs) -- structure-aware chunking gets you most of the benefit
for a fraction of the cost.

## The one-sentence summary

Chunk along the boundaries that already carry meaning in your document, keep chunks
focused on one idea, and measure the result instead of guessing.
