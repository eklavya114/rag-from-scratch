# Day 3: Vector Databases

Day 2 gave us embeddings and a way to compare two of them with cosine similarity.
Today's problem: what happens when you have a million documents instead of six?

## What is a vector database, really?

A vector database is just a library that's really good at one specific job: given a
new embedding, find the embeddings already stored that are most similar to it, fast.

That's it. It's not thinking. It's not "understanding" anything. It's a specialized
search index, the same way a normal database is really good at finding rows where
`user_id = 42`. A vector database is really good at finding rows where "this vector
is close to that vector."

Under the hood it still just stores embeddings and metadata (like the original text,
a title, a URL). The only difference from Day 3's `SimpleVectorDB` below and a real
one is *how* they search: ours checks every single item, real ones use clever
shortcuts to avoid that.

## Why we even need them

Yesterday, `comparison.py` compared a query embedding against 6 documents. Checking
all 6 took no time at all.

Now imagine 1 million documents. Checking a query against every single one, one at a
time, means 1 million cosine similarity calculations, every single time someone asks
a question. That's called **brute force search**, and it works fine at small scale
but falls apart as your data grows — it gets slower in a straight line with the
number of documents you have.

A vector database's whole purpose is to avoid checking everything. It organizes the
data ahead of time so it can skip huge chunks of irrelevant vectors and only check
the ones that are actually likely to be close matches.

## How they work at a basic level

You don't need to become an expert in this to use a vector database, but here's the
gist of the two ideas you'll see mentioned everywhere:

**IVF (Inverted File Index)** — group similar vectors into "buckets" ahead of time
(like sorting books into sections: fiction, history, science). When a search comes
in, figure out which bucket it probably belongs to, and only search inside that
bucket instead of the whole library.

**HNSW (Hierarchical Navigable Small World)** — build a map of "neighbor" connections
between vectors, a bit like a social network. To search, you start somewhere and hop
from neighbor to neighbor, always moving toward closer matches, until you can't get
any closer. You never have to touch most of the vectors — you just follow a trail
toward the best ones.

Both approaches trade a little bit of accuracy (you might occasionally miss the
absolute best match) for a massive gain in speed. That trade-off is usually well
worth it — the difference between "instant" and "unusably slow" at real scale.

## Real vector databases people actually use

- **Pinecone** — fully managed, cloud-hosted, no infrastructure to run yourself. Good
  for teams that want to move fast and not think about servers.
- **Milvus** — open source, self-hosted (usually via Docker), built for very large
  scale. Good if you want full control and don't mind running it yourself.
- **Weaviate** — open source, available self-hosted or managed, comes with extra
  features like built-in hybrid search (keyword + vector combined).
- **Chroma** — lightweight, open source, great for local development and smaller
  projects, easy to get running in minutes.
- **FAISS** — not really a "database" so much as a library (from Meta) for fast
  similarity search. Often used as the engine *inside* other tools.

We'll look at code examples for a few of these in `real_vector_dbs.py`, without
needing an actual API key to read and understand them.

## What we're building today

- `simple_vector_db.py` — a real, working vector database class, using brute force
  search, so the concept is completely transparent.
- `indexing_basics.py` — a simplified indexing approach compared against brute force,
  with an actual timing benchmark.
- `real_vector_dbs.py` — example code for Pinecone, Milvus, and Weaviate, so you know
  what using a real one looks like.
- `practical_example.py` — Day 1's documents + Day 2's embeddings + today's vector
  database, all wired together into one working search system.
- `benchmark.py` — numbers showing how search speed changes as the dataset grows.
- `notebook.ipynb` — a full walkthrough tying the whole week together.

## Why this matters for RAG

Every RAG system needs a place to store document embeddings and search them quickly.
That place is a vector database. Without one, a RAG system with any real amount of
data would be too slow to use — every single question would mean scanning your
entire document collection from scratch.

The vector database is the piece that makes RAG *practical* at scale, not just
possible in a demo with 6 documents.
