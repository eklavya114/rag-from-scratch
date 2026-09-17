# Day 1: RAG Basics

Okay so you want to know what RAG actually is. Let's talk about it like normal humans, no jargon.

## What is RAG, really?

Imagine you're taking an exam. There are two ways to do it:

1. **Memorize everything and hope you remember it.** This is basically what a plain LLM does. It learned a bunch of stuff during training, and it answers your question using only what's stuck in its "brain." If it never learned something, or it misremembers, tough luck.

2. **Bring a library into the exam room.** You don't have to memorize everything. When someone asks you a question, you walk to the shelf, pull out the exact book (or page) that has the answer, read it, and then answer using that.

RAG is option 2. It stands for **Retrieval-Augmented Generation**, but really it just means: "look stuff up before you answer."

So instead of an AI just guessing from memory, a RAG system:
- Takes your question
- Goes and finds documents that are actually relevant to it (retrieval)
- Hands those documents to the AI along with your question
- The AI reads them and writes an answer (generation)

That's it. That's the whole idea. Retrieval + Generation = RAG.

## Where is this actually used?

You've probably used RAG systems without knowing it:

- **Customer support chatbots** that answer questions using your company's actual docs, instead of making stuff up
- **"Chat with your PDF"** tools — upload a contract or textbook, ask it questions, it answers from that specific file
- **Coding assistants** that search your codebase before suggesting a fix, instead of guessing blind
- **Search engines with AI summaries** (like when Google gives you a paragraph answer instead of just links)
- **Internal company tools** that let employees ask questions about HR policy, engineering docs, or product specs

Basically anywhere you want an AI to answer using *your* specific, up-to-date information instead of whatever it happened to learn months or years ago during training.

## Why does this even matter?

A couple of big reasons:

- **LLMs don't know your private data.** They've never seen your company's internal wiki. RAG lets them "read" it on the fly.
- **LLMs go stale.** Their knowledge has a cutoff date. RAG lets them use fresh info, updated today, without retraining anything.
- **LLMs hallucinate.** They sometimes confidently make things up. Giving them real source documents to work from makes answers way more grounded and trustworthy.
- **It's cheaper than retraining.** Retraining a model on new data is expensive and slow. Updating a folder of documents is instant and free.

## What we're building today

Nothing fancy — just enough to see the idea work with your own eyes. In this folder:

- `simple_rag.py` — a tiny RAG system built with plain Python. No AI APIs, no vector databases, no external libraries. It has a handful of sample documents, searches them by keyword, ranks the matches, and generates a simple templated answer.
- `examples.py` — five example questions run through the system, so you can see what good retrieval, bad retrieval, and "I don't know" all look like.
- `test_basic.py` — a few simple tests to check retrieval, ranking, and generation are actually doing what they should.

This is intentionally simple. Real RAG systems use embeddings and vector databases to find "meaning," not just keywords. We'll get there later in the 30 days. Today is about getting the core idea to click.

## How to run it

You just need Python. No installs, no API keys, nothing.

```bash
# Run the main demo
python simple_rag.py

# Run the 5 examples
python examples.py

# Run the tests
python test_basic.py
```

That's it. Go run `simple_rag.py` first and watch it answer a question using only the documents it has.
