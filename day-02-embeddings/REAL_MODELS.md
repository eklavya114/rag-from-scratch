# Notes on Real Embedding Models

Everything in this folder uses fake, hand-picked embeddings so you could see the
math clearly. Real embedding models work the same way at the math level (cosine
similarity, comparing vectors) — the only thing that changes is *how the numbers
get generated in the first place*. Here's a quick, honest rundown.

## How real models generate embeddings

A real embedding model is trained on huge amounts of text. It learns, statistically,
which words tend to appear in similar contexts, and slowly builds a numeric space
where related words and ideas land near each other. Nobody writes these numbers by
hand — they're learned automatically from data.

Instead of 4 or 5 numbers like our examples, real embeddings usually have **hundreds
or thousands** of dimensions. More dimensions means more room to capture subtle
shades of meaning.

## Popular real embedding models

- **OpenAI's `text-embedding-3-small` / `text-embedding-3-large`** — API-based, easy
  to use, good general-purpose quality.
- **Sentence-Transformers (`all-MiniLM-L6-v2`, etc.)** — open source, runs locally,
  great for getting started without needing an API key.
- **Cohere Embed** — API-based, strong multilingual support.
- **Voyage AI embeddings** — API-based, often used specifically for RAG systems.

You'll usually pick one based on: cost, whether you want it running locally vs. via
an API, and how big your documents are.

## What changes when you use a real model

1. Instead of hand-picking numbers, you call the model with your text, and it
   returns the embedding for you: `embedding = model.embed("your text here")`.
2. The embeddings are much longer (hundreds of numbers instead of 4-6).
3. The similarity math is **exactly the same** — cosine similarity works the same
   way whether the vector has 4 numbers or 1536 numbers.
4. You'll usually store these in a **vector database** (Pinecone, Chroma, FAISS,
   Weaviate) so you can search across thousands or millions of documents quickly,
   instead of comparing one-by-one like we did today.

## What stays exactly the same

- The core idea: similar meaning -> similar numbers.
- The core operation: cosine similarity (or a close cousin like dot product or
  Euclidean distance) to measure how close two embeddings are.
- The core RAG pattern: embed your documents once, embed the incoming query, find
  the closest documents, hand them to the LLM.

Everything we built today with fake embeddings is a scaled-down, honest preview of
what happens under the hood in a production RAG system. Later in this 30-day
project, we'll swap in a real embedding model and see the exact same code patterns
apply.
