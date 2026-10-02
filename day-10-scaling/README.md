# Day 10: Scaling RAG

Everything through Day 9 was built and tested against 6 documents. That's fine for
learning the ideas, but real systems don't stay at 6 documents -- they grow to
thousands, then hundreds of thousands, then sometimes millions. Today is about what
actually breaks when that happens, and what to do about it.

## Why scaling matters

A RAG system that works great in a demo with a handful of documents can fall apart
completely once real usage kicks in: more documents to search, more users asking
questions at once, more data to store and keep fresh. If you only ever test at toy
scale, you'll find out about scaling problems in production, from real users,
instead of in testing -- which is the most expensive way to find out.

## The challenge: what actually breaks as you grow

Growing from 1,000 documents to 1,000,000 documents doesn't just mean "a bit
slower." Several specific things degrade, often at different rates:

- **Latency** — brute-force comparing a query against every document gets slower
  roughly in proportion to how many documents you have (we measured this directly
  back on Day 3). At some point, "proportional to document count" becomes
  unacceptably slow.
- **Memory** — every embedding has to live somewhere. A million embeddings, even at
  a modest size each, adds up to real memory pressure.
- **Cost** — embedding a million documents (and re-embedding whenever they change)
  costs real money, and so does the compute to search across them.
- **Throughput** — a system that answers one question in 50ms might completely
  fall over when 1,000 people ask questions in the same second.

## Scaling bottlenecks

Today we're specifically going to measure, not just describe, four categories of
bottleneck:

1. **Latency** — how search time grows as document count grows.
2. **Memory** — how much RAM a growing index actually consumes.
3. **Cost** — what embedding and storing a growing document set actually costs.
4. **Throughput** — how many queries per second a system can sustain.

## What we're testing today

- `scaling_benchmarks.py` — real latency/memory/cost numbers from 100 to 100,000
  documents, so "it gets slower" becomes an actual measured curve.
- `indexing_impact.py` — brute force vs. simple partitioning vs. HNSW-style
  indexing (building on Day 3's work), proving indexing stops being optional past a
  certain scale.
- `batching_and_parallelization.py` — sequential vs. batched vs. parallel
  processing, measured.
- `caching_strategies.py` — caching queries, embeddings, and rankings, with real
  hit-rate numbers.
- `sharding_and_distribution.py` — splitting data and queries across multiple
  "servers" (simulated), and the complexity cost that comes with it.
- `query_optimization.py` — rewriting, early termination, and approximation,
  measured for their actual speed/quality tradeoff.
- `cost_analysis_at_scale.py` — embedding, storage, and compute costs as document
  count grows, with concrete numbers.
- `monitoring_at_scale.py` — tracking percentiles (not just averages), alerting,
  and what actually matters to watch.
- `notebook.ipynb` — a full walkthrough tying it together.

## Strategies to handle it

Scaling isn't solved by throwing bigger hardware at the problem (though sometimes
that's part of it) -- it's solved by smarter design:

- **Indexing** instead of brute-force search, so search time stops growing
  linearly with data size.
- **Caching** so repeated work doesn't get redone.
- **Batching and parallelization** so throughput isn't limited by doing one thing
  at a time.
- **Sharding** so no single machine has to hold everything.
- **Monitoring** so you find out about degradation from a dashboard, not from
  angry users.

The theme for today: scaling is a design discipline, not a hardware upgrade.
