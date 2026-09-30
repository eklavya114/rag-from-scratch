# Retrieval Quality Best Practices

A quick reference for measuring retrieval quality on a real system, beyond the toy
examples in this folder.

## Build ground truth from real queries, labeled by hand

Ground truth created by re-reading actual documents and honestly deciding what's
relevant is slow, but it's the only kind you can trust. Ground truth inferred
automatically from the system you're trying to evaluate just tests the system
against itself, which proves nothing.

## Cover a real spread of difficulty, not just the easy cases

An evaluation set made entirely of queries that share exact keywords with their
answer documents will make almost any retriever look great -- and tell you nothing
about how it handles real, awkwardly-phrased user questions. Deliberately include
queries that don't share vocabulary with the source text.

## Report several metrics together, never just one

Precision, recall, NDCG, MRR, and MAP each answer a different question. A retriever
can score well on one and poorly on another -- reporting only one metric hides
exactly the kind of problem the others would have caught.

## Always deduplicate to unique documents before scoring

If your retriever returns multiple chunks from the same document, collapse to
unique document IDs before computing any metric. These metrics assume a relevant ID
can only be "found" once; feeding them raw duplicated chunk IDs can silently inflate
scores past their intended range (a real bug we hit and fixed on Day 6).

## Break results down by category before trusting the average

An overall score of 0.85 can hide a real, specific weakness -- like every "medium"
difficulty or "conceptual" query underperforming while "easy" queries carry the
average. Breaking down by difficulty and query type turns a vague number into an
actionable target.

## Debug specific failing queries, not just the aggregate trend

When you find a weak query, actually look at what was retrieved versus what should
have been, and inspect why (embedding overlap, missing vocabulary, chunking
boundaries). A root-cause hypothesis from one concrete failure is worth more than
staring at a dropping average.

## Evaluate every pipeline stage separately

Score retrieval alone, then retrieval+ranking, then the full generation pipeline,
rather than only measuring the end-to-end result. A metric that doesn't move after
adding a stage isn't necessarily wasted effort -- it can mean an earlier stage
already got it right.

## Never assume one approach is universally better — measure it on your data

"Semantic search beats keyword search" is a reasonable prior, not a law. On Day 8's
own small test set, keyword search actually won on NDCG, because a real weakness in
our specific concept-embedding approach happened to misfire on a specific query.
The only way to know which approach is actually better for YOUR system is to
measure both on YOUR data.

## Track every benchmark run, with a label

Every evaluation run should be saved with what it represents (a date, a commit
hash, a config version), so future runs can be compared against a real baseline.
Without that history, you can't tell whether today's score of 0.75 is an
improvement or a regression from last month.

## The one-sentence summary

You cannot reliably improve a RAG system's retrieval by eyeballing outputs --
build honest ground truth, measure multiple metrics against it, and let the
numbers -- not intuition -- tell you what to fix next.
