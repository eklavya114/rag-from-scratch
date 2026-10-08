# Day 14 Best Practices: Caching and Performance Optimization

## Cache what's actually expensive and actually repeats

Caching only pays off when both are true: the thing you're caching costs
real time/money to recompute, AND it gets asked for again. `cache_warming.py`
and `integration_with_previous_days.py` both showed this directly: a
94% hit rate on skewed traffic (a few popular queries dominating) produced
a double-digit speedup, because the skew meant most requests really were
repeats. On uniformly random, never-repeating traffic, a cache is pure
overhead with nothing to show for it.

## Measure before optimizing, not after

`performance_profiling.py` exists specifically because intuition about
where time goes is often wrong, or right only by coincidence of the
current scale and shape of the system. Profile per-stage, identify the
actual bottleneck, and only then decide where caching (or any other
optimization) is worth the complexity it adds.

## Cache at the right layer

`caching_framework.py`'s multi-level design (query cache, ranking cache)
exists because a full-pipeline cache miss doesn't mean every stage has
to redo its work -- a ranking-level cache can still save work even when
the overall query is new. Cache at every layer where meaningful,
independent reuse is possible, not just at the outermost boundary.

## Pick the eviction strategy to match the traffic shape

`cache_eviction_strategies.py` showed LFU outperforming LRU on stable,
popularity-skewed traffic (67.8% vs 51.8% hit rate) because LFU protects
genuinely popular keys from eviction even when they haven't been accessed
*most recently*. LRU would be the better choice for traffic with shifting
recency patterns instead of stable popularity. There's no universally
best eviction policy -- there's only the one that matches your actual
access pattern.

## Exact-match caching misses obvious near-duplicates

`similarity_based_caching.py` showed that a plain dictionary cache misses
on "What is RAG?" vs "Why does RAG matter?" even though they'd often
deserve the same cached answer. A similarity-based cache catches these
at the cost of a similarity computation on every lookup and a threshold
that has to be tuned carefully -- too loose and you serve wrong answers,
too tight and you're back to exact-match-only.

## Invalidate exactly as broadly as what changed, no broader

`cache_invalidation.py` is the most failure-prone part of caching for a
reason: invalidating too little serves stale data, invalidating too much
(e.g. wiping the whole cache on any change) throws away perfectly valid
entries and tanks your hit rate for no reason. Document edits and
embedding-model upgrades are *different* invalidation triggers needing
different keys (`VersionedCache`'s document-version tracking vs
`ModelVersionedEmbeddingCache`'s `(text, model_version)` keys) -- don't
try to force one mechanism to track a trigger it wasn't built for.

## Monitor hit rate as a trend, not a single number

`cache_statistics.py` showed an overall 50% hit rate hiding a real
degradation from 90% down to 10% as traffic composition shifted.
Windowed tracking (the same percentile-over-average discipline as Day
10's latency monitoring) catches regressions an all-time average masks
for a long time.

## Distributed caches need an explicit shared tier

`distributed_caching.py` showed that without a shared remote cache, every
server pays the same cold-miss cost independently -- there's no "free"
sharing of cached work across a fleet. A two-tier local+remote design
gets most of local caching's speed most of the time, while still letting
a miss on one server become a hit via another server's prior work.

## The speedup comes from the hit rate, not from caching making real work faster

`integration_with_previous_days.py` made this explicit: average latency
on a cache MISS in the cached pipeline was statistically the same as the
uncached pipeline's average latency. Caching doesn't make the underlying
retrieval/ranking/generation work itself faster -- it lets you skip that
work entirely on a hit. The entire benefit is a function of how often you
get to skip it.
