# Day 4: Chunking

Days 1-3 gave us documents, embeddings, and a place to store and search them. There's
a problem we quietly skipped over: our documents were tiny, a couple sentences each.
Real documents aren't. Today we fix that.

## Why we even need chunking

You can't hand a 100-page PDF to an embedding model and get back one useful number
for the whole thing. A few reasons:

- Embedding models have a size limit on how much text they can process at once.
- Even if they didn't, cramming an entire document into one embedding averages
  everything together. A 100-page PDF probably covers dozens of different topics --
  squashing all of that into a single vector loses almost all of the detail.
- When you retrieve something, you want to hand the LLM a focused, relevant piece of
  text, not an entire book. Nobody wants to read 100 pages to answer one question.

So before we can embed and store a document, we need to break it into smaller
pieces first. That's chunking: splitting a big document into smaller pieces, each
one small enough to embed well and specific enough to be useful when retrieved.

## What happens with bad chunking

Imagine cutting a pizza with your eyes closed. You might slice straight through a
topping, leave one piece mostly crust, or cut a piece so small it's just a sliver of
cheese. Bad chunking does the same thing to text:

- **Broken sentences**: a chunk ends mid-sentence, so neither half makes sense on
  its own. "The main cause of the outage was a database migra" ... cut right there.
- **Lost context**: a chunk contains an answer, but not the question or topic it's
  answering. You get "...and that's why it takes 3 seconds," with no idea what "it"
  refers to.
- **Mixed topics**: a chunk accidentally spans the end of one section and the start
  of a completely different one, confusing the embedding and the retrieval.

When chunks are bad, embeddings of those chunks are bad, and retrieval built on top
of bad embeddings is bad. Garbage in, garbage out.

## What happens with good chunking

Good chunking is like slicing a pizza properly: each slice is a complete, useful
piece on its own. Applied to text:

- Each chunk contains one complete idea, or a small number of closely related ideas.
- Chunks respect natural boundaries -- sentence endings, paragraph breaks, section
  headers -- instead of cutting wherever a character count happens to run out.
- When a chunk gets retrieved on its own, it still makes sense without the rest of
  the document around it.

Good chunking makes every later step of RAG work better: cleaner embeddings, more
accurate retrieval, and answers the LLM can actually generate correctly.

## Real world chunking strategies

- **Fixed-size chunking**: split every N characters or words, no matter what's
  there. Simple and fast, but it doesn't care about sentence or paragraph
  boundaries -- it will cut mid-sentence without a second thought.
- **Sentence-based chunking**: split at sentence boundaries, then group a few
  sentences together per chunk. Never cuts a sentence in half.
- **Paragraph-based chunking**: split at paragraph breaks. Naturally groups related
  sentences together, since paragraphs are usually already one idea.
- **Chunking with overlap**: let neighboring chunks share a bit of text at the
  boundary, so if an idea spans two chunks, some context carries over into both.
- **Semantic chunking**: instead of following character counts or punctuation, group
  sentences together based on whether they're actually *about the same thing*, using
  embeddings to measure that. The smartest approach, and the most expensive to run.

None of these is "correct" in every situation -- they're tools with different
tradeoffs, and picking the right one depends on the kind of document you're working
with (more on that in `real_world_examples.py`).

## What we're building today

- `chunking_strategies.py` — five different chunking methods, implemented and shown
  running on a sample document.
- `chunking_comparison.py` — the same document, chunked five different ways, with a
  side-by-side comparison of chunk count, average size, and broken sentences.
- `semantic_chunking.py` — a similarity-based chunking approach using Day 2's
  embeddings, grouping sentences that are actually related.
- `real_world_examples.py` — chunking strategies matched to different document
  types: docs, news, legal text, research papers, and support Q&A.
- `chunk_quality.py` — actual metrics for measuring whether a set of chunks is good
  or bad, instead of just eyeballing it.
- `notebook.ipynb` — a full walkthrough tying it all together.

## Why chunking quality affects RAG quality

Everything downstream depends on chunks. Bad chunks make bad embeddings (Day 2).
Bad embeddings make bad matches in the vector database (Day 3). Bad matches mean the
LLM gets the wrong context, or the right context with half a sentence missing, and
generates a worse answer.

Chunking is easy to overlook because it feels like a small, boring preprocessing
step. In practice, it's one of the highest-leverage things you can tune in a RAG
system -- often more impactful than swapping to a fancier embedding model.
