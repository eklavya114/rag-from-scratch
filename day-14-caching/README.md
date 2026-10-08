# Day 14: Caching and Performance Optimization

This is the final day of Week 2. Day 10 introduced caching as one of several
scaling techniques. Today caching gets its own full day, because it's arguably the
single highest-impact optimization available for a RAG system -- more impactful,
dollar for dollar, than almost any other change covered so far.

## Why caching matters so much

Real query traffic isn't uniformly random. In most real systems, a small number of
popular questions account for a large fraction of total traffic -- the exact "long
tail" distribution Day 10's caching_strategies.py simulated. Depending on the
product, it's genuinely common for 70-80%+ of queries to be exact repeats or close
variations of something already asked recently.

That means a cache isn't a nice-to-have for an edge case -- it's doing real work on
the MAJORITY of your traffic, every day. Every cache hit is a query that skips
embedding, skips vector search, skips ranking, and skips generation entirely,
turning a multi-step pipeline into a single dictionary lookup.

## The challenge: when to cache, when not to

Caching sounds simple (store the answer, reuse it next time) but gets genuinely
hard fast:

- Cache WHAT, exactly -- the raw query text? A normalized version? The embedding?
  The final answer?
- For HOW LONG -- forever, until memory runs out, until the underlying documents
  change?
- What happens when the SAME question is asked in slightly different words?
- What happens when the documents a cached answer was based on get updated?

Get these wrong and a cache either provides little benefit (too strict, rarely
hits) or actively serves stale, wrong answers (too loose, never invalidated).

## Different types of caching

- **Query result caching** — cache the final answer for an exact (or
  near-exact) query.
- **Embedding caching** — cache the embedding for a piece of text, so repeated
  text never gets re-embedded.
- **Ranking result caching** — cache the ranked order for a given
  (query, candidate set) pair.

Each layer sits at a different point in the pipeline, and a cache hit at an
earlier layer skips more downstream work than a hit at a later one.

## The caching tradeoff: speed vs. freshness

Every cache is a bet that what was true a moment ago is still true now. That bet
usually pays off -- documents and embeddings don't change every second -- but when
it doesn't, a cache actively serves outdated information faster than ever. The
entire discipline of cache invalidation (today's `cache_invalidation.py`) exists to
manage exactly this tradeoff deliberately, instead of leaving it to chance.

## What we're testing today

- `caching_framework.py` — a real multi-level cache architecture: query results,
  embeddings, and ranking, each with its own get/set.
- `similarity_based_caching.py` — reusing a cached answer for a DIFFERENT but
  similar query, not just an exact match.
- `cache_eviction_strategies.py` — LRU, LFU, TTL, and hybrid eviction, measured for
  memory impact.
- `cache_warming.py` — pre-populating a cache with common queries before real
  traffic arrives.
- `embedding_caching.py` — the specific, high-impact case of caching embeddings.
- `cache_statistics.py` — hit rate, miss rate, size, and a simple dashboard.
- `distributed_caching.py` — local vs. remote caching and the coherence problem.
- `cache_invalidation.py` — what to do when the underlying documents actually
  change.
- `performance_profiling.py` — finding the REAL bottleneck instead of guessing.
- `integration_with_previous_days.py` — caching wired into the full Day 1-13
  pipeline, measured end to end.
- `notebook.ipynb` — a full walkthrough tying it together.

Caching is one of the rare optimizations that's both high-impact and relatively
simple to reason about -- today is about implementing it properly instead of just
knowing it exists.
