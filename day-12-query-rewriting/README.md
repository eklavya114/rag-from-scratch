# Day 12: Query Rewriting and Expansion

Days 1-11 built retrieval, ranking, generation, evaluation, and context management
-- a genuinely complete RAG pipeline. All of it assumed the query coming in was
already reasonable. Today questions that assumption: what happens when it isn't?

## Why query quality matters

Garbage in, garbage out. If the query handed to retrieval is vague, typo-ridden,
oddly phrased, or genuinely ambiguous, even a perfect retrieval and ranking system
can only find the best match FOR THAT BAD QUERY -- which might be nowhere near
what the user actually wanted to know.

Everything built through Day 11 optimizes what happens AFTER a query arrives.
Query rewriting is about improving the query itself, before any of that machinery
even runs.

## The challenge: users aren't search experts

Real users don't write queries like a search engineer would. They type things
like:

- "rag" instead of "What is Retrieval-Augmented Generation?"
- "why slow" instead of "Why is my vector database search taking so long?"
- "vektor database" (typo) instead of "vector database"
- "difference between X and Y and when to use each" (several questions at once)
- "python" (genuinely ambiguous -- the language? a snake? a variable named that?)

None of this is a user doing something wrong. It's just how people actually type
when they're not thinking about how a search system works. A RAG system that only
works well for perfectly-phrased queries will frustrate real users constantly.

## How rewriting helps

Query rewriting takes the user's original, possibly rough query and transforms it
into something more likely to retrieve well -- sometimes by cleaning it up,
sometimes by expanding it with related terms, sometimes by breaking it into
smaller pieces, sometimes by generating several different phrasings and trying
them all. The user still typed what they typed; the system just stops taking it
too literally.

## Different rewriting strategies

- **Basic cleaning** — lowercase, strip stopwords, expand known abbreviations, fix
  common typos.
- **Synonym expansion** — add related words so a query matches documents that used
  different wording for the same idea.
- **Decomposition** — split a multi-part question into separate sub-questions,
  search each, and merge the results.
- **Semantic rewriting** — detect what KIND of query this is (a definition
  request, a comparison, a how-to) and rephrase to match how documents of that
  kind tend to be written.
- **Expansion techniques** — broaden or narrow a query deliberately (more general,
  more specific, more context) depending on what's likely to help.
- **Pseudo-relevance feedback** — run the query once, look at what came back, and
  use that to improve the query for a second pass.
- **Ambiguity resolution** — detect when a query could genuinely mean more than
  one thing, and handle that explicitly instead of guessing silently.

## What we're testing today

- `basic_rewriting.py` — cleaning, stopword removal, abbreviation expansion, typo
  fixing.
- `synonym_expansion.py` — a synonym dictionary generating query variations,
  measured against Day 8's evaluation framework.
- `decomposition_rewriting.py` — splitting compound questions and merging results.
- `semantic_rewriting.py` — intent detection and structure-aware rephrasing.
- `query_expansion_techniques.py` — generalizing, specializing, and context-adding
  expansion.
- `pseudo_relevance_feedback.py` — learning from a first retrieval pass to improve
  a second one.
- `ambiguity_resolution.py` — detecting and handling genuinely ambiguous queries.
- `integration_with_previous_days.py` — rewriting wired into the full retrieval
  pipeline, measured end to end.
- `notebook.ipynb` — a full walkthrough tying it together.

Users aren't search experts, and they shouldn't have to be. A good RAG system
meets them where they are -- today is about building the layer that does that.
