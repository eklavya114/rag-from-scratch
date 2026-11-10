# Retrospective

## What worked well

Building strictly on the standard library forced every idea to be
explained at its simplest, honest level: a bag-of-concepts embedding
instead of a trained model, a Python list with cosine similarity
instead of a real vector database. Nothing could hide behind a library
doing the real work invisibly. Importing real code from earlier days
into every later day, rather than ever copying it, also paid off
directly: a bug fixed once (the duplicate Day 22 Config collision found
on Day 29, say) stayed fixed everywhere, and reusing Day 8's real
evaluation metrics across Days 21, 26, and 28 meant "better" always
meant something measured, not assumed.

## What was hard

The toy embedding vocabulary was consistently the most fragile piece.
It was built once, on Day 2, around a Python and RAG topic vocabulary,
and every later day that needed a different domain (Day 22's support
knowledge base, Day 28's domain adaptation, Day 29's complete system)
had to notice that mismatch and build its own small, honest replacement
rather than silently reusing something that would have returned zero
results for every query. That exact failure was caught directly while
building Day 29's pipeline: every single support document embedded to
an all-zero vector under the original vocabulary. A second hard spot was occasional Windows-specific
flakiness in a couple of HTTP demos, a real OS-level connection reset
unrelated to any logic bug, fixed with a small retry.

## What I would change next time

Build one small, shared domain-aware embedding helper earlier, around
Day 9 or Day 14, instead of letting each later day that needed a
different vocabulary rebuild its own version of the same fix. The
pattern was right every time it appeared, it just appeared more than
once because nothing earlier had generalized it.

## The three most important lessons

**Measure before trusting.** Every claim about an improvement, caching,
ranking weights, a vocabulary change, a prompt tweak, only became
trustworthy once it was checked against real, held-out metrics. A
confident-sounding claim and a measured fact are not the same thing,
and several real bugs in this project were caught exactly where a
narrative claim stopped matching the actual printed output.

**Import, never copy.** Code copied between days drifts, a fix in one
copy never reaches the other. Code imported between days stays
consistent by construction, and a module-name collision caught during
Day 29's integration is proof the discipline works: it surfaced a real
bug that copying would have silently hidden instead.

**Honesty about limits is a feature, not an apology.** Stating plainly
that this project has no real embedding model, no real vector database,
and no real LLM is not a weakness. It is what makes every other claim
in this project, the metrics, the security checks, the evaluation
results, actually trustworthy, since nothing here is pretending to be
more than it honestly is.
