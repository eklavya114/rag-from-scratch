# Day 13: Hallucination Prevention

Days 1-12 built a complete, measurable, query-aware RAG pipeline. Today addresses
the failure mode that makes an otherwise-great RAG system actually dangerous to
ship: the generator confidently stating something that isn't true.

## What are hallucinations?

A hallucination is when a language model states something as fact that isn't
actually supported by its sources -- or isn't true at all. It's not the model
"lying" (it has no concept of truth to violate); it's the model doing what it
always does, predicting plausible-sounding text, in a case where "plausible" and
"true" have quietly come apart.

This is a real, well-documented problem with real language models, not a
hypothetical edge case. It happens even in RAG systems, which are specifically
designed to reduce it by grounding answers in retrieved documents -- grounding
helps a lot, but it doesn't make hallucination impossible. A model can still:

- State a fact confidently that the retrieved documents never actually said.
- Blend two separate facts from two different documents into one incorrect claim.
- Fill in a plausible-sounding detail when the real answer was "the documents don't
  say."

## Why they're dangerous

Wrong information stated with confidence is often worse than no information at
all. A user who gets "I don't know" knows to look elsewhere. A user who gets a
confident, wrong answer may act on it directly -- and RAG's whole credibility
proposition (that it's more trustworthy than a model answering from memory alone)
collapses the moment it hallucinates just as confidently as a model with no
grounding at all.

## Common hallucination patterns

- **Fabricated specifics** — inventing a date, number, or name that sounds right
  but was never in any source.
- **Source blending** — correctly stating two separate facts, but incorrectly
  attributing one fact's detail to the other's subject.
- **Overconfident extrapolation** — the sources imply something close to an
  answer, and the model states the full answer as if it were directly confirmed.
- **Silence-filling** — when the honest answer is "the documents don't address
  this," generating a plausible-sounding guess instead.

## How RAG helps prevent them

Grounding generation in retrieved documents (Days 1-7) is the first and biggest
defense -- an answer built from real text is far less likely to drift than one
generated purely from a model's internal memory. But grounding alone isn't
enforcement: nothing stops a generator from adding a plausible detail the sources
never actually stated. Today's techniques go further: actively checking whether
each claim in an answer is actually supported, instead of just hoping grounding
was enough.

## What we're testing today

- `hallucination_detection.py` — checking generated claims against source
  documents and flagging unsupported ones.
- `claim_extraction.py` — identifying what counts as a factual claim that needs
  checking in the first place.
- `source_verification.py` — matching a specific claim to the specific document
  that does (or doesn't) support it.
- `uncertainty_expression.py` — calibrating HOW an answer is phrased to match how
  confident the grounding actually is.
- `contradiction_detection.py` — handling the case where sources disagree, instead
  of silently picking one side.
- `grounding_enforcement.py` — actively blocking or rewriting answers that contain
  unsupported claims.
- `fact_checking_pipeline.py` — the full loop: generate, extract claims, verify,
  score, revise.
- `integration_with_previous_days.py` — wiring this into the Day 1-7 generation
  pipeline, measured before and after.
- `notebook.ipynb` — a full walkthrough tying it together.

Hallucinations are a real, measurable problem, and -- as today will show -- a
measurably addressable one. The goal isn't a system that never hallucinates (no
current technique fully guarantees that); it's a system that catches far more of
it than a system doing nothing about it at all, and is honest about what it
doesn't know instead of confidently guessing.
