# Context Window Management Best Practices

A quick reference for managing context windows in a real RAG system, beyond the
toy examples in this folder.

## Always budget explicitly, don't guess

Compute the actual fixed cost (system prompt, query, conversation history,
reserved response space) before deciding how much room is left for documents.
Guessing at "probably enough room" leads to either silent truncation or wasted
budget you could have used for one more relevant document.

## Match selection strategy to the query shape

A narrow, specific question is usually served best by relevance-first selection.
A broad "tell me about X, Y, and Z" question benefits from coverage or diversity
selection, which guarantee breadth that pure relevance ranking won't. Picking the
wrong strategy for the query shape wastes budget either way — on near-duplicates
for narrow queries, or on irrelevant breadth for specific ones.

## Use a real tokenizer once it matters

Word-based estimation is fine for a rough sketch, but the gap between estimate and
reality can be large — especially for technical content, code, or
punctuation/number-heavy text. Once you're actually deciding what fits in a hard
limit (not just estimating roughly), use the real tokenizer for your model family.

## Prefer summarizing over dropping, but verify the summary is actually working

A shortened version of a highly relevant document is usually better than losing it
entirely. But naive extractive summarization can fail in non-obvious ways — as we
found in this folder's own multi-turn example, where a running summary could get
"stuck" re-selecting old sentences instead of folding in new content. Check that a
summarization step is actually preserving what you think it's preserving, not just
assume it.

## Don't assume more context means a better answer

Measure it. Past a certain point, adding less-relevant documents can measurably
dilute an answer rather than improve it — the diluting content is still technically
"grounded" in a real source, which is exactly why a naive groundedness check alone
won't catch the problem. Find where quality plateaus or declines for your own
queries and documents, the same way `quality_analysis_by_context.py` did here.

## Reserve multi-turn for genuine necessity, not convenience

Breaking a question into multiple turns adds real cost: more API calls, more
latency, and a harder design problem (reliably carrying context forward without
it growing unboundedly or silently losing information). Reach for it when a
single call's context window genuinely can't hold what's needed — not as a
default way to avoid thinking carefully about selection and compression first.

## Treat context budget as a design constraint, not an afterthought

Decide your selection strategy, compression approach, and fallback behavior (what
happens when nothing more fits) as part of designing the system, not as a patch
applied after hitting a context-length error in production.

## The one-sentence summary

Context is a scarce, shared resource — budget it explicitly, select and compress
deliberately based on the actual query, and measure whether more context is
actually helping before assuming it is.
