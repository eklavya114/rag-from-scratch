# Retrieval Best Practices

A quick reference for retrieval decisions once you're building a real RAG system,
beyond the toy examples in this folder.

## Always measure retrieval, don't just eyeball it

Use precision@K, recall@K, and NDCG (see `retrieval_metrics.py`) against a set of
known test cases -- queries where you already know which documents should come
back. Retrieval quality is easy to assume and easy to get wrong; measuring it is
the only way to know whether a change (new embedding model, different chunk size,
adjusted top_k) actually helped or hurt.

## Start simple, add complexity only when it earns its keep

A plain embedding-search retriever (`basic_retriever.py`) is a reasonable default.
Add complexity in this rough order, only when metrics show you need it:

1. **Query preprocessing** — cheap, usually safe, often helps.
2. **Hybrid search** (keyword + semantic) — catches real gaps in pure semantic
   search, worth it for most production systems.
3. **Multi-query retrieval** — more expensive (multiple searches per question), best
   reserved for cases where recall really matters and single-query performance is
   measurably weak.
4. **Custom re-ranking** (recency, position, business rules) — add once you have a
   solid base retriever and specific evidence that raw similarity ranking isn't
   producing the order you want.

## Pick top_k deliberately

Too small (`top_k=1`) means one bad match ruins the whole answer. Too large
(`top_k=20`) floods the LLM with mostly irrelevant context, which can dilute the
answer or increase cost. A common starting range is 3-5 chunks, tuned based on how
big your chunks are and how much the LLM's context window can comfortably hold.

## Always handle the "no good match" case explicitly

A retriever that always returns its top_k results, even when none of them are
actually relevant, sets the LLM up to hallucinate a confident-sounding answer from
irrelevant context. Check similarity against a minimum threshold (see
`practical_retriever.py`) and have a clear "I don't have relevant information for
that" path.

## Confidence scores are for humans and downstream logic, not just decoration

Attaching a confidence label (high/medium/low) to retrieval results makes it easy to:
- Decide whether to even call the LLM, versus returning "not found" directly.
- Show users how much to trust an answer.
- Log and monitor retrieval quality over time in production.

## Retrieval and ranking are two different jobs

Retrieval's job is recall: find a good pool of candidates using similarity, cast a
reasonably wide net. Ranking's job is precision: decide the best final order using
similarity plus whatever else actually matters (recency, source trustworthiness,
document type). Don't conflate them -- a retriever that tries to also be a perfect
ranker often ends up being neither.

## Test on realistic, not just convenient, queries

It's tempting to only test with queries that are worded similarly to your
documents. Test with real, awkwardly-phrased, ambiguous questions too -- that's
where query preprocessing, multi-query, and hybrid search earn their cost, and
where a purely embedding-based retriever's weaknesses actually show up.
