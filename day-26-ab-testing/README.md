# Day 26: A/B Testing and Continuous Improvement

## The problem

"I think this change is better" is a guess until you measure it. A new
`top_k`, a tweaked ranking weight, a different prompt template, any of
these can genuinely help, genuinely hurt, or make no real difference at
all, and gut feeling cannot reliably tell those three apart. The only
way to know is to actually compare the old version and the new version
against real usage, side by side, and look at the numbers.

## What an A/B test is, in plain words

Split incoming traffic into two groups. Group A keeps using the current
version. Group B gets the new version. Everything else about how each
group is treated stays identical. After enough traffic has gone through
both, compare the outcomes. The only difference between the two groups
was the thing being tested, so any real difference in outcomes can be
attributed to that change, not to anything else.

## Why random assignment matters

If you let users choose their own group, or you split by something like
"new users get B," the two groups stop being alike in every way except
the change itself. Maybe new users ask simpler questions. Maybe people
who opt in to try new things are just more patient with a weaker answer.
Random assignment is what makes the two groups statistically similar to
begin with, so a difference you measure afterward is actually caused by
the change, not by who ended up in which group.

## Why you need enough samples before trusting a result

Flip a fair coin 10 times and getting 7 heads would not be shocking.
Flip it 10,000 times and getting 7,000 heads would be very strong
evidence the coin is not fair. The same logic applies to comparing two
variants: a small sample can easily show one variant "winning" by pure
chance, even when there is no real difference at all. Today's
significance check exists specifically to tell "this looks different"
apart from "this is reliably different."

## What we're building today

A variant router that assigns users to version A or B consistently, a
simulated user population with a real (but noisy) preference between the
two versions, a metric comparison across more than one signal at once,
a significance check that separates a real effect from luck, a sample
size planner for deciding how much data is enough before starting, a
safe staged rollout with guardrails, and an experiment log that records
every decision made along the way.

## How this connects to Day 8 and Day 21

Day 8 built real retrieval quality metrics, precision, recall, NDCG,
on a labeled test set. Today's `metric_comparison.py` reuses those exact
metrics to compare variant A and variant B on retrieval quality, not
just on simulated user feedback. Day 21's `regression_check.py` compared
a new agent version against a saved baseline and printed PASS or FAIL.
Today's significance check is the natural next step past that: instead
of just comparing two numbers and asking whether one is bigger, it asks
whether the difference is large enough, given how much data was
collected, to actually trust.

## The bakery analogy

A bakery wants to know if a new cookie recipe is actually better than
the old one. It gives half of today's customers the old recipe and half
the new one, picked at random so it is not just regulars getting one and
strangers getting the other, and counts who comes back next week for
more. One day of sales would not prove much either way. A few weeks of
consistent, meaningfully higher repeat business from the new recipe is
real evidence. Today's work builds exactly that process for a RAG
service: split the customers, serve each group consistently, and wait
for enough real evidence before changing the whole menu.
