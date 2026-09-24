# Vector Database Comparison

A quick reference for picking a vector database, once you're ready to move past
`SimpleVectorDB` and use something production-ready.

## Feature and pricing comparison

| Database | Hosting | Open Source | Free Tier | Best For | Pricing Model |
|---|---|---|---|---|---|
| **Pinecone** | Fully managed | No | Yes, limited | Fast setup, no infra to manage | Pay per stored vector + query volume |
| **Milvus** | Self-hosted (or Zilliz Cloud managed) | Yes | Free if self-hosted | Very large scale, full control | Free (self-hosted) or usage-based (Zilliz Cloud) |
| **Weaviate** | Self-hosted or managed | Yes | Yes, limited (managed) | Hybrid keyword + vector search | Free (self-hosted) or usage-based (managed) |
| **Chroma** | Local / in-process, or hosted | Yes | Free (local) | Prototyping, small-to-medium projects | Free (local) or usage-based (hosted) |
| **FAISS** | Library, embedded in your app | Yes | Always free | Building a custom search engine | Free (you run and maintain it) |

## How to think about the trade-offs

**Managed vs. self-hosted**
Managed (Pinecone, managed Weaviate) means someone else runs the servers, handles
scaling, and you pay for convenience. Self-hosted (Milvus, self-hosted Weaviate,
Chroma, FAISS) means you run it yourself, which is free but means you're responsible
for uptime, backups, and scaling it as your data grows.

**Scale**
Chroma and FAISS are great for prototypes and small-to-medium datasets. Milvus is
specifically built for very large scale (billions of vectors) if you eventually get
there. Pinecone and Weaviate sit comfortably in between and scale well without much
tuning on your part.

**Extra features**
Weaviate's hybrid search (combining keyword search and vector search in one query)
is genuinely useful — remember from Day 2's `comparison.py` that keyword search and
embedding search each catch different things. Combining them often beats using
either alone.

## A simple decision guide

- **Just experimenting, want zero setup?** Start with Chroma.
- **Building a real product, don't want to manage servers?** Pinecone.
- **Need to combine keyword and vector search?** Weaviate.
- **Expecting massive scale, want full control and no vendor lock-in?** Milvus.
- **Building your own custom search tool from scratch?** FAISS, as a library inside
  your own code.

## The pattern that stays the same everywhere

No matter which one you pick, you'll always be doing the same two things we built
today in `SimpleVectorDB`:

1. `add(embedding, metadata)` — store a vector and whatever data you want attached
   to it.
2. `search(query_embedding, top_k)` — find the closest stored vectors to a new one.

Everything else (indexing algorithm, hosting, pricing, extra features) is really
just different implementations of that same core idea.
