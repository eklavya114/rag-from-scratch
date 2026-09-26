# Ranking Best Practices

A quick reference for ranking decisions once you're building a real RAG system,
beyond the toy examples in this folder.

## Don't rank on similarity alone

Similarity tells you how topically close a chunk is to a query -- nothing else. It
doesn't know if a chunk is outdated, low quality, or a near-duplicate of something
already shown. A production ranker almost always needs at least one more signal
(recency, source trust, or quality) combined in, even if the weights are modest.

## Tune weights against real evaluation data, don't guess

`combined_ranking.py`'s auto-tuner is a toy version of a real practice: pick weights
by testing them against labeled examples of what a good ranking actually looks like
for your use case, not by intuition. A recency weight that helps time-sensitive
queries can measurably hurt timeless ones (see `integration_test.py`'s third
example) -- the only way to know is to measure both.

## Always measure ranking quality, separately from retrieval quality

Use NDCG, MRR, and MAP (`ranking_evaluation.py`) specifically against your ranking
output, not just your retrieval output. It's possible for retrieval to find all the
right candidates while ranking still puts them in a bad order -- the two need to be
evaluated independently to know which one to improve.

## Watch for duplicate-ID double-counting

If your retrieval step returns multiple chunks from the same document, collapse to
unique document IDs before computing NDCG/MRR/MAP -- these metrics assume each
relevant ID can only be "found" once. Feeding them raw, duplicated chunk results can
silently inflate scores past their intended range (we hit exactly this bug building
`ranking_vs_no_ranking.py`).

## Diversity matters more than it seems

A top-5 list where 3 results are near-duplicates of each other effectively wastes
those 3 slots -- the user (or LLM) gains nothing from seeing the same information
three times. A modest diversity penalty (see `advanced_ranking.py`) that nudges a
different, still-relevant result into the list is usually worth more than a
marginal similarity improvement from picking the single "best" near-duplicate.

## Make ranking decisions explainable

Track which signal drove each result's final position (`practical_ranker.py`'s
`dominant_signal`). This isn't just a debugging nicety -- when a ranking looks
wrong in production, "recency drove this" vs. "quality drove this" tells you
exactly which weight to adjust, instead of guessing at a black box.

## Handle edge cases explicitly

Empty result lists, single-result lists, and exact ties all need defined behavior,
not accidental behavior that falls out of whatever the sort happens to do. A ranker
that crashes (or silently misbehaves) on an empty list is not production-ready, no
matter how good its scoring logic is.

## The one-sentence summary

Retrieval finds the right pool of candidates; ranking decides what actually gets
seen -- treat both as equally important, equally measurable, and equally worth
tuning deliberately.
