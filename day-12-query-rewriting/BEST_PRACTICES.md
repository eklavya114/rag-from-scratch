# Query Rewriting Best Practices

A quick reference for query rewriting decisions on a real RAG system, beyond the
toy examples in this folder.

## Always keep the original query available

Every rewriting technique in this folder works by TRANSFORMING or ADDING TO the
original query, never by discarding it outright. A rewrite can be wrong — keeping
the original as a fallback (or searching with both) protects against a bad rewrite
making things worse than doing nothing at all.

## Cheap fixes first, expensive techniques only when needed

Basic cleaning (typos, abbreviations, stopwords) is nearly free and catches a
surprising number of real failures. Reach for decomposition, pseudo-relevance
feedback, or multi-variant generation only once the cheap fixes have been applied
and a real gap remains — not as a default for every query.

## Measure rewriting's impact, don't assume it

Every technique in this folder was checked against real retrieval results, and
more than one first attempt didn't show the effect it was supposed to — usually
because the specific example chosen didn't actually exercise the mechanism. Use
Day 8's evaluation framework (precision, recall, NDCG, MRR, MAP) to confirm a
rewriting strategy helps on your actual data, rather than trusting that it
"should" help because the idea sounds reasonable.

## Attribute improvement to the right stage

When rewriting and ranking are both in the pipeline, measure each stage's
contribution separately (as `integration_with_previous_days.py` does here).
Crediting the full pipeline's improvement to whichever technique you're most
excited about — instead of measuring what each stage actually added — makes it
easy to over-invest in the wrong place going forward.

## Decomposition needs a real multi-part question

Splitting on a joining word like "and" is a cheap heuristic that can over-trigger
on single-topic queries that just happen to contain that word. Guard against this
(e.g. requiring each split piece to be a substantial standalone fragment) before
trusting a decomposition to actually represent separate questions.

## Pseudo-relevance feedback trusts its own first pass — know the risk

PRF assumes the top first-pass results are relevant without any verification. This
is a reasonable bet when the first pass was already in the right neighborhood, and
a risky one when it wasn't — PRF can double down on an already-wrong direction.
It's a refinement technique, not a rescue for badly off-topic retrieval.

## Detect ambiguity from the system's own uncertainty

You don't need to understand a query's meaning to detect that it might be
ambiguous — a close score race between genuinely different top documents is a
cheap, honest, measurable signal. Prefer surfacing that uncertainty (via a
clarifying question, or searching multiple interpretations) over silently
committing to one guess.

## Synonym and expansion quality depends on your embedding model's actual vocabulary

An expansion word only helps if the underlying similarity function can recognize
it. With a real, well-trained embedding model, this is rarely a constraint. With
any system using a narrower or more specialized embedding approach, choose
expansion terms deliberately with that system's actual behavior in mind — don't
assume every synonym will register as meaningfully "close."

## The one-sentence summary

Query rewriting exists because real users don't write search-optimized queries —
apply it in layers from cheapest to most sophisticated, keep the original as a
fallback, and measure every technique's real effect before trusting it.
