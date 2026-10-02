# Scaling Best Practices

A quick reference for scaling decisions on a real RAG system, beyond the toy
examples in this folder.

## Measure before you optimize

Every technique in this folder was demonstrated with real benchmark numbers, not
assumptions. Before adding indexing, caching, sharding, or any other scaling
technique to a real system, measure your actual bottleneck first — optimizing the
wrong layer wastes real engineering effort without fixing the problem users
actually experience.

## Don't reach for complexity before you need it

Sharding, distributed architectures, and aggressive approximation all add real
operational and debugging complexity. Each is worth it once you've genuinely hit
the scale where simpler approaches break down — not by default, and not because a
system "might" get big someday. A single well-indexed machine handles a surprising
amount of real-world scale on its own.

## Indexing is not optional past a certain size

Brute-force search latency grows roughly linearly with document count. This is
fine at hundreds or a few thousand documents, and a genuine production problem well
before a million. Treat indexing as a required part of the design once your
document count is growing, not an optimization to add later.

## Caching and batching are close to free — use them by default

Caching repeated work and batching to amortize fixed overhead cost essentially
nothing in exchange for real speed and cost savings. Unlike indexing or
approximation, there's rarely a reason NOT to do both wherever your system has
repeated queries or many independent calls to make.

## Approximate only with a measured quality cost in hand

Early termination and approximate (sampled) search can meaningfully speed up
search, but both trade away some exactness. Measure the actual quality gap on your
own data (the same way Day 8's evaluation framework measures retrieval quality)
before trusting an approximation in a context where a wrong or missing result has
real consequences.

## Compute cost scales with both data size AND query volume

Storage and embedding costs are easy to estimate and often modest. Compute cost
(search latency × query volume) can grow much faster, especially with
unindexed search — it's often the fastest-growing cost category, not the most
obvious one. Budget for it as it scales, not as a fixed line item.

## Monitor percentiles, not averages

An average latency of 85ms can hide a p99 latency approaching a full second — a
real, painful experience for a meaningful fraction of users that the average
completely conceals. Track p50, p95, and p99 (or higher), plus error rate, cache
hit rate, and resource headroom, and alert on concrete thresholds rather than
relying on someone happening to notice.

## Sharding solves a real problem, but creates new ones

Sharding is what enables scale beyond a single machine's memory and compute, but
it introduces scatter-gather complexity, routing logic, rebalancing, and harder
debugging. It's the right tool once you've actually outgrown a single well-indexed,
well-cached machine — not a default starting architecture.

## The one-sentence summary

Scaling is a design discipline — index instead of brute force, cache and batch
aggressively, approximate only with a measured cost, shard only once you need to,
and monitor the metrics that actually reveal degradation before your users do.
