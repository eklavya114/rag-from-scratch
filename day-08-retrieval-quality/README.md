# Day 8: Retrieval Quality

Welcome to Week 2. Days 1-7 built a complete RAG pipeline: chunk, embed, store,
retrieve, rank, generate. It works. But "it works" and "it works well" are very
different claims, and so far we've only been eyeballing the difference.

## Why measuring retrieval matters

You wouldn't ship a car without testing the brakes. You wouldn't ship a bridge
without load-testing it. But it's shockingly easy to ship a RAG system after only
checking "does it return something that looks reasonable for my 3 example
queries" -- and then be surprised when it quietly fails for real users on real
questions.

You can't improve what you don't measure. If you don't know your retrieval's
precision, recall, and ranking quality as actual numbers, you have no way to know
whether a change you made (a new embedding approach, a different chunk size, a
tuned ranking weight) made things better or worse. You're just guessing.

## The challenge: how do you even know if retrieval is "good"?

"Good" isn't a single number. A retrieval system can:

- Find the right documents, but bury them at position 8 (bad ranking).
- Rank the right documents perfectly, but only find half of what's actually
  relevant (bad recall).
- Return lots of documents that all seem plausible, but only one is actually right
  (bad precision).

None of these failure modes look identical, and none of them are caught by simply
reading a handful of example outputs and nodding. You need actual ground truth --
knowing, in advance, which documents SHOULD come back for a given query -- and
actual metrics to compare against it.

## Different metrics tell different stories

- **Precision@K** answers: "of what we returned, how much was actually relevant?"
- **Recall@K** answers: "of everything relevant that exists, how much did we find?"
- **MAP** (Mean Average Precision) answers: "across the whole result list, how well
  did we do at putting relevant results near the top, on average?"
- **NDCG** (Normalized Discounted Cumulative Gain) answers: "did we rank the MOST
  relevant results highest, not just find them somewhere?"
- **MRR** (Mean Reciprocal Rank) answers: "how quickly did a user find their first
  good answer?"

A retriever can score well on one of these and poorly on another. Knowing which
metric moved (and which didn't) tells you exactly what kind of problem you have.

## Real-world examples

**Bad retrieval, silently**: a support bot that answers refund questions using a
years-old pricing page, because that page happens to share more keywords with the
question than the current one -- and nobody ever measured recall against a
labeled test set to catch it.

**Good retrieval, measurably**: a documentation search that's been evaluated
against 50 real user questions with known correct answers, tracked over time as
the underlying embedding model and chunking strategy changed, so every change was
a measured improvement instead of a guess.

## What we're building today

- `evaluation_framework.py` — a reusable `EvaluationDataset` and
  `evaluate_retriever()` function, the foundation everything else builds on.
- `metrics_explained.py` — a deep, example-driven walkthrough of precision,
  recall, MAP, NDCG, and MRR.
- `test_dataset_creation.py` — how to build good ground truth, including
  difficulty levels.
- `metric_visualization.py` — text-based charts for interpreting results at a
  glance.
- `metric_analysis.py` — breaking performance down by query type and finding
  patterns in failures.
- `per_query_diagnosis.py` — debugging exactly why one specific query failed.
- `benchmark_suite.py` — reproducible benchmarks you can re-run as the system
  changes.
- `retriever_comparison.py` — keyword vs. semantic vs. hybrid vs. multi-query,
  measured side by side.
- `integration_with_previous_days.py` — evaluating the actual Day 1-7 pipeline.
- `notebook.ipynb` — a full walkthrough tying it together.

## Why this is production critical

Once real users depend on a RAG system, "it seemed to work in my testing" isn't
good enough. You need to know, with numbers: is retrieval getting better or worse
as documents get added, as the embedding model changes, as chunking gets tuned?
Evaluation is what turns RAG development from guesswork into engineering -- it's
the difference between hoping a change helped and knowing it did.
