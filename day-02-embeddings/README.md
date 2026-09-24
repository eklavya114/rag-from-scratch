# Day 2: Embeddings

Yesterday we built a RAG system that finds documents by matching keywords. It worked, but it was dumb in one specific way: it only understands exact words. Today we fix that.

## What are embeddings, really?

An embedding is just a word (or sentence, or whole document) turned into a list of numbers.

That's it. That's the whole idea. "Dog" becomes something like `[0.2, 0.8, -0.1, 0.4]`. "Cat" becomes something like `[0.3, 0.7, -0.2, 0.5]`. Notice those two lists of numbers look kind of similar? That's not an accident — it's the entire point.

Think of it like giving every word a set of coordinates on a map. Words with similar meaning end up near each other on that map. Words with different meanings end up far apart. "Dog" and "cat" live in the same neighborhood (animals, pets, four legs). "Dog" and "car" live in completely different neighborhoods.

## Why do computers need numbers instead of words?

Computers are really good at math and really bad at "understanding" language the way we do. A computer can't tell you that "happy" and "joyful" mean almost the same thing just by looking at the letters — the words don't even share most of the same characters.

But if you turn "happy" and "joyful" into numbers, and those numbers end up close together, now the computer can do math to figure out they're related. It can measure the distance between them. It can rank things by how close they are. It can search by meaning instead of by spelling.

Numbers are a language computers already speak fluently. Embeddings are just a translation layer between human words and computer math.

## Similar words get similar numbers

Here's the part that feels like magic the first time you see it: words that mean similar things end up with similar embeddings, even though nobody manually typed those numbers in.

Real embedding models learn this by reading huge amounts of text and noticing which words tend to show up in similar situations. "Cat" and "dog" both show up near words like "pet," "vet," "leash," and "food," so the model learns to place them close together. "Cat" and "car" almost never show up in the same kind of sentence, so they end up far apart.

Today we're not training a real model (that's a much bigger topic). Instead, we'll hand-craft some simple fake embeddings just to prove the concept: similar words get similar numbers, and we can measure that similarity with math.

## Where you've already used this

You've used embeddings today, probably without knowing it:

- **Google Search** doesn't just match your exact words anymore. Search "cheap flights" and it can surface a page that says "affordable airfare" — because those phrases have similar embeddings.
- **Netflix and Spotify recommendations** represent shows, movies, and songs as embeddings, then recommend things that are "close" to what you already liked.
- **Spam filters** compare the embedding of your email to embeddings of known spam, instead of just checking for a list of banned words.
- **Chatbots and RAG systems** (like the one we started building yesterday) use embeddings to find documents that are relevant to your question, even if you didn't use the exact same words as the document.

## What we're building today

- `embedding_basics.py` — hand-made fake embeddings for a handful of words, plus a cosine similarity function to measure how close two embeddings are.
- `visualization.py` — a text-based way to "see" which words cluster together, without needing any charting library.
- `comparison.py` — Day 1's keyword search vs. an embedding-based search, run side by side on the same queries, so you can see exactly where keyword search falls short.
- `notebook.ipynb` — a step-by-step walkthrough tying all of it together.

## How embeddings power RAG

Remember the retrieval step from Day 1? That's the part that decides which documents are relevant to your question. Yesterday we did that with keyword matching — count how many words overlap.

Real RAG systems do that step differently:

1. Every document gets turned into an embedding, once, ahead of time.
2. When a question comes in, the question also gets turned into an embedding.
3. The system compares the question's embedding to every document's embedding, and picks the ones that are closest.

Because embeddings capture *meaning* and not just *spelling*, this catches cases keyword search misses. Someone could ask "How do I make my app faster?" and the system can retrieve a document about "improving performance" — even though not a single word matches — because the two phrases live near each other in embedding space.

That's the real upgrade embeddings bring to RAG: retrieval based on what you *mean*, not just what you *typed*.

## How to run it

Still no installs needed, just plain Python.

```bash
# See fake embeddings and similarity scores in action
python embedding_basics.py

# See which words cluster together
python visualization.py

# Compare keyword search vs embedding search side by side
python comparison.py

# Or open the notebook and run it cell by cell
jupyter notebook notebook.ipynb
```
