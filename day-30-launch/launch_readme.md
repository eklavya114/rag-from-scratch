# RAG From Scratch

A complete Retrieval-Augmented Generation system, built one real piece
at a time over 30 days, using only the Python standard library. No
API keys, no GPU, and no internet connection are needed to run any
part of it. Every stage a real RAG system needs, retrieval, ranking,
generation, evaluation, production hardening, security, and a working
complete project, is here, readable, and runnable.

## How to start in 3 steps

1. Clone this repository.
2. From `day-29-complete-system/`, run `python main.py` to build the
   whole system and answer three sample questions with their sources.
3. From the same folder, run `python tests.py` to verify the parts of
   the project that must never break.

## A learning path

Start with `day-01-rag-basics/` and `day-02-embeddings/` to see the
core idea in its simplest form: a question, a search, an answer. Read
through in order up to `day-07-generation/` for the full basic
pipeline. From there, `day-08-retrieval-quality/` shows how to measure
whether any of it is actually good. If you care about production
systems specifically, jump to `day-22-production-rag/` through
`day-27-security-privacy/`, that stretch covers a real service, a real
API, monitoring, failure handling, A/B testing, and security. Finish at
`day-29-complete-system/` to see every piece connected into one
runnable whole.

## What this is not

This project uses toy embeddings (a small, hand-built set of word
concepts, not a trained model), a toy vector store (a Python list with
cosine similarity, not a real indexed database), and no real language
model (answers come from templates and real retrieved text, never from
an LLM). It is not a security audit either, Day 27's security work is
real and useful teaching material, but it is not a substitute for a
professional review before handling real user data. None of this is
pretending to be production-grade AI. It is honest, working code built
to teach exactly how every piece fits together.

## How to contribute or extend

Every day's folder is self-contained and imports from earlier days
rather than copying code, so adding a new day or improving an existing
one is mostly a matter of following that same pattern: a README, a
BEST_PRACTICES.md, runnable scripts, and a notebook that ties them
together. `day-30-launch/next_steps.md` lists the concrete next moves
if you want to turn this toy system into something closer to a real
one: a real embedding model, a real vector database, a real language
model, real monitoring, and a real secrets manager, each one a
reasonable next project on top of what is already here.
