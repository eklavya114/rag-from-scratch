# Day 18 Best Practices: Agent Memory

## Keep short-term small

`short_term_memory.py` bounds the conversation window on purpose. A
window that grows without limit eventually stops fitting in a prompt,
and most of a long conversation stops being relevant to the current
step well before that point. A small, fixed window keeps the agent
focused on what's actually recent.

## Save only stable facts

`memory_update_rules.py`'s `is_stable_fact` check exists because not
everything said in a conversation deserves to persist. A preferred
contact method is worth remembering across sessions. A passing comment
about today's mood is not, and treating it as a permanent trait
produces an agent that acts on information that was never meant to
last.

## Let users correct and forget

`memory_update_rules.py` overwrites a fact when it's corrected instead
of keeping both the old and new value side by side, since two
conflicting facts about the same thing is worse than either one alone.
`forget_fact` honors a removal request unconditionally, with no
stability or sensitivity check, since removing information is never
the risky direction.

## Never store secrets

`memory_update_rules.py`'s sensitive-data check refuses to save
anything matching a card number or similar pattern, regardless of how
naturally it came up in conversation. Long-term memory is exactly the
wrong place for information that should never persist in the first
place.

## Retrieve fewer, better memories

`memory_retrieval.py` ranks every candidate memory against the current
task and keeps only a small budget of the best matches, the same
retrieve-then-limit shape as document retrieval back on Day 6. Every
fact or episode included in a prompt competes for the model's
attention. A handful of genuinely relevant memories beats dumping
everything ever recorded.

## Treat episodic memory as a log, not a summary

`episodic_memory.py` records what happened, with a timestamp and
structured detail, rather than trying to compress history into a
running narrative. A log can always be searched and ranked later. A
summary has already thrown away the details that might turn out to
matter.

## Memory goes stale, so confirm before trusting old facts

`memory_staleness.py` showed the middle ground between two bad
extremes: trusting a fact forever regardless of age, or re-confirming
every fact on every use. A staleness threshold lets an agent trust a
recently confirmed fact without asking again, while still
double-checking anything old enough that it might no longer be true.
