# Day 11: Context Window Management

Day 10 scaled the data side of RAG: more documents, more throughput, more servers.
Today scales down to a much smaller, much more immediate constraint: the box an
LLM can actually read from in a single call, and how to use every inch of it well.

## What is a context window?

A context window is the maximum amount of text an LLM can read and respond to in
one request, measured in tokens (roughly, pieces of words -- more on that in
`token_counting.py`). Everything has to fit inside it: your system prompt, the
conversation so far, the retrieved documents you're handing over, the user's
question, AND enough room left over for the model's actual answer.

Think of it like a suitcase with a hard weight limit. It doesn't matter how much
useful stuff you own -- only what fits in the suitcase makes the trip.

## Why it matters

Days 1-10 built retrieval and ranking systems that can find dozens of relevant
chunks for a question. But you can't just hand an LLM every relevant chunk you
found -- there's a hard ceiling on how much text fits in one call, and anything
past that ceiling either gets rejected outright or silently truncated, depending
on the API.

Worse, even when something technically fits, cramming the context window full of
marginally-relevant material can make an LLM's response WORSE, not better --
burying the one chunk that actually answers the question in a pile of chunks that
don't (we'll measure this directly in `quality_analysis_by_context.py`).

## Different models have different limits

Context window sizes vary a lot, and they've grown dramatically over time:

- Early GPT-3.5-era models: around 4,000 tokens -- roughly 3,000 words.
- GPT-4 class models: commonly 8K-128K tokens depending on the version.
- Modern long-context models (Claude, Gemini, and others): can reach into the
  hundreds of thousands of tokens, some over a million.

A bigger window gives you more room, but it's not a free pass: bigger context
still costs more (most APIs charge per token), takes longer to process, and -- as
we'll measure today -- doesn't automatically produce a better answer just because
it's technically possible to stuff more in.

## The challenge

Given a fixed token budget, how do you decide:

- Which documents actually make the cut?
- Should you trim or summarize documents to fit more of them in?
- When does adding another document stop helping and start hurting?
- How do you handle a case that genuinely needs MORE context than any single
  call allows?

## What we're testing today

- `context_budget_calculator.py` — working out exactly how much room is left for
  documents once the system prompt, query, and response space are accounted for.
- `document_selection_strategies.py` — relevance-first, importance-first,
  diversity-first, and coverage-first selection, compared.
- `summarization_techniques.py` — extractive, abstractive-style, and key-point
  compression, measured for quality vs. compression ratio.
- `token_counting.py` — simple word-based estimation vs. a real tokenizer, and how
  far off the estimate actually is.
- `iterative_context_optimization.py` — starting with the best documents and
  adjusting (add more, or summarize) based on remaining budget.
- `multi_turn_strategy.py` — handling cases where one call's worth of context
  genuinely isn't enough.
- `quality_analysis_by_context.py` — measuring where answer quality plateaus (or
  drops) as you add more documents, proving more isn't always better.
- `notebook.ipynb` — a full walkthrough tying it together.

Context is precious. Every token spent on a marginally-relevant document is a
token not spent on the response, and -- as we'll show -- can actively work against
the answer you're trying to get. Today is about spending that budget deliberately.
