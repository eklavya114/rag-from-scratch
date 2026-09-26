# Day 6: Ranking

Day 5 gave us retrieval: finding a pool of documents that are plausibly relevant to
a question. Today's problem: that pool usually isn't in the right order yet, and
order matters more than people expect.

## What is ranking, really?

Ranking is deciding the order results appear in, from most relevant to least.

Retrieval's job is to find good candidates. Ranking's job is to put the single best
one first, the second best one second, and so on. They sound similar, but they're
different jobs -- a system can retrieve all the right documents and still fail if
it puts the best one at position 8 instead of position 1.

## Why ranking matters so much

Think about Google. A search for "best pizza near me" might technically match
millions of pages. Nobody looks at a million results -- they look at the first 3 to
5, maybe scroll a little further, and almost never go past page one.

RAG has the exact same problem, just compressed. A vector database might return the
top 20 "relevant" chunks for a question, but an LLM's context window (and your
wallet, since more context costs more) means you can usually only afford to hand
over the top 3 to 5. If the actually-best chunk is sitting at position 8, it might
as well not exist -- the LLM never sees it, and the answer suffers exactly as if
retrieval had missed it entirely.

Good retrieval with bad ranking still produces bad answers.

## The challenge: what makes something "relevant"?

Similarity to the query is the obvious signal, and it's the one we've used so far
(Days 2, 3, and 5). But it's not the only thing that matters, and sometimes it's
not even the most important thing:

- A chunk can be highly similar to the query but out of date.
- Two chunks can be equally similar, but one comes from a source people actually
  trust and the other doesn't.
- A user asking about "the latest pricing" wants the newest matching document, even
  if an older one happens to score slightly higher on pure similarity.

Real ranking has to combine several signals, weigh them sensibly, and adjust based
on what kind of question is being asked.

## Ranking signals

- **Similarity score** — how close the chunk's embedding is to the query's (what
  we've used through Day 5).
- **Recency** — how new the document is. Matters a lot for time-sensitive
  questions, barely at all for timeless ones.
- **Popularity** — how often a document has been used, clicked, or cited. A signal
  that other people found it useful before.
- **Quality** — ratings, reviews, or other signals about how good the content
  itself is, independent of whether it matches this particular query.
- **Source trustworthiness** — some sources are simply more reliable than others,
  and that should count for something.
- **Diversity** — avoiding a results list that's 5 near-duplicate chunks saying the
  same thing, when a slightly less similar but different chunk would serve the user
  better.

None of these alone is "the" right way to rank. The right combination depends on
the use case.

## What we're building today

- `basic_ranker.py` — a `Ranker` class with separate similarity, recency, and
  quality ranking strategies, shown side by side.
- `scoring_strategies.py` — six individual scoring signals, each demonstrated on its
  own.
- `combined_ranking.py` — weighted combinations of signals, and how changing the
  weights changes the final order.
- `ranking_evaluation.py` — NDCG, MRR, and MAP: real metrics for measuring whether
  a ranking is actually good.
- `advanced_ranking.py` — diversity, context-awareness, and domain-specific ranking
  rules.
- `practical_ranker.py` — a ranker built to handle real-world messiness: ties,
  single results, empty lists.
- `ranking_vs_no_ranking.py` — a direct, measured comparison proving that ranking
  quality matters as much as retrieval quality.
- `integration_test.py` — the full pipeline, Days 1 through 6, wired together.
- `notebook.ipynb` — a complete walkthrough tying everything together.

## How ranking connects to retrieval and generation in RAG

The full RAG pipeline, as this project has built it, looks like:

1. **Chunk** documents (Day 4) so they're a manageable size.
2. **Embed** the chunks (Day 2) so they can be compared by meaning.
3. **Store and retrieve** (Day 3, Day 5) to pull back a pool of plausible candidates
   for a given question.
4. **Rank** (today) that pool into the best possible order, using whatever signals
   actually matter.
5. **Generate** an answer, using only the top few ranked chunks -- everything the
   LLM sees comes from what ranking decided was worth showing it.

Ranking is the last checkpoint before generation. Whatever it gets wrong, the LLM
has no way to correct -- it can only work with what's put in front of it.
