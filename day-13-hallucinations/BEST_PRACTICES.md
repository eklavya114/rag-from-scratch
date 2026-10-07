# Hallucination Prevention Best Practices

A quick reference for hallucination prevention decisions on a real RAG system,
beyond the toy examples in this folder.

## Check claims individually, never the whole answer as one block

A whole-answer average can hide one fabricated sentence sitting among several
well-grounded ones. Split an answer into claims and verify each independently —
this is the difference between "this answer is 90% grounded, roughly" and "this
specific sentence is the problem."

## Filter out non-claims before verification

Questions, opinions, and vague filler sentences were never meant to be checked
against sources the same way a factual assertion is. Sending every sentence
through source verification wastes effort and can produce misleading
"unsupported" flags on sentences that were never claims in the first place.

## Trace claims to a specific source, not just "grounded somewhere"

Knowing a claim is supported by SOME document is weaker than knowing which one.
Per-document verification enables real citation, and it's what lets you notice
when two different documents both plausibly support a claim with genuinely
different numbers or details — a contradiction worth surfacing, not averaging away.

## Calibrate confidence expression — don't just hedge-or-don't

A system with only two modes (confident statement, or generic hedge) throws away
real information. Match the phrasing to the actual confidence band: state firmly
when well-grounded, hedge proportionally when moderately grounded, and say "I
don't know" outright when there's essentially nothing to go on — these are
different situations and deserve different language.

## Never silently resolve a contradiction you can't actually resolve

If two sources disagree on a specific fact (a price, a date, a count), surfacing
both — with an honest "I can't determine which is correct from the text alone" —
is more useful than confidently picking one, especially when picking wrong has
real consequences (pricing, medical, legal).

## Choose enforcement strictness deliberately

Loose enforcement (report, don't change the answer) is useful for monitoring and
staged rollout — see what WOULD be caught before changing user-facing behavior.
Strict enforcement (remove or rewrite unsupported claims, fall back to "I don't
know" when nothing is grounded) actually protects users, at the cost of sometimes
producing a shorter or more fragmented answer. This is a product decision as much
as a technical one.

## Measure the real metric, not a convenient one

More than one technique in this folder initially looked like it made things
worse, purely because the wrong metric was being used to check it — a whole-answer
word-overlap score can legitimately DROP after fact-checking removes a fabrication
and replaces it with an honest "I don't know," since that honesty statement is
itself built from words no source used. Measure average confidence across actual
factual claims, not blanket word overlap across an entire answer including its own
boilerplate.

## A toy word-overlap check is a floor, not a ceiling

The detection techniques in this folder (word-overlap against sources) reliably
catch the cruder failure mode — a claim built mostly from words that never
appeared anywhere. They can be fooled by a claim that reuses real source WORDS to
assert something false (source blending). A production system should pair this
kind of cheap, fast check with a more capable verifier (an NLI model, or an LLM
specifically prompted to check entailment) for claims that matter enough to
justify the extra cost.

## The one-sentence summary

Hallucination prevention is a correction, not a quality tradeoff — detect claim by
claim, verify against specific sources, express confidence honestly, and measure
the actual improvement rather than assuming grounding alone was ever going to be
enough.
