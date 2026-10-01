# Embedding Model Selection Best Practices

A quick reference for choosing and operating an embedding model in a real RAG
system, beyond the toy examples in this folder.

## Measure on your own data before trusting a benchmark

A model that tops a general leaderboard isn't guaranteed to be best for your
specific documents and queries. Use Day 8's evaluation framework to run a real,
measured comparison on your own ground truth before committing to a model.

## Start with a cheap, fast general-purpose model

Unless you already have evidence of a quality gap, a small general-purpose model
(like `text-embedding-3-small`) is a reasonable default: cheap, fast, and good
enough for most retrieval tasks. Upgrade to a larger or specialized model only once
you've measured a real, persistent quality problem it would actually fix.

## Revisit the choice — it's not a one-time decision

Embedding model choice is easy to pick once and never reconsider. It's also one of
the highest-leverage changes available in a RAG system. Periodically re-evaluate
against newer models as they become available, especially if your evaluation
metrics have plateaued.

## Specialized models win inside their domain, not outside it

A legal-specialized or medical-specialized model can decisively beat a
general-purpose model within its specialty, but has no inherent advantage (and
sometimes real degradation) outside it. Only reach for a specialized model when
you're confident your actual document set lives squarely in that domain.

## Treat caching and batching as free wins, always worth doing

Caching avoids re-embedding identical text, and batching amortizes fixed
per-call overhead across many items. Neither costs any retrieval quality — there's
essentially no reason not to do both in any real system.

## Treat quantization and dimensionality reduction as a measured tradeoff

Both can meaningfully cut storage and search cost at scale, but both introduce some
precision loss. Measure the actual quality impact (with Day 8's framework) on your
real data before adopting either — don't assume the tradeoff is negligible just
because it looks small on paper.

## Compute the real local-vs-API breakeven for your volume

Don't default to either option without doing the math. API cost scales with usage;
local hosting cost is largely fixed. At low-to-moderate volume, APIs are usually
cheaper; at very high volume, or with an expensive model tier, self-hosting can
genuinely win. Privacy and compliance requirements can override the cost
calculation entirely.

## Fine-tune only against a diagnosed, specific gap

The most effective fine-tuning projects start from a concrete failure found through
real evaluation and diagnosis (like Day 8's per_query_diagnosis.py), not a vague
goal of "better embeddings." Fine-tuning against a diffuse, unmeasured problem risks
spending real effort without fixing anything you can point to.

## The one-sentence summary

Pick an embedding model by measuring it on your own data against your own ground
truth, not by assumption or reputation — and keep measuring as your documents,
queries, and the available models all change over time.
