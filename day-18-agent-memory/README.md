# Day 18: Memory Systems for Agents

Day 17 made an agent's reasoning visible. Today is about making its
memory real: short-term, long-term, and episodic memory, so an agent
stops asking the same questions over and over.

## The problem: an agent that forgets everything is exhausting

Every agent in Days 15 through 17 started each run from a blank slate.
That's fine for a single, self-contained task, but it breaks down the
moment an agent interacts with the same user more than once. Ask it
your preferred contact method today, and tomorrow it asks again. Tell
it an order was already refunded, and next week it opens a duplicate
ticket. A system with no memory cannot build on anything it already
knows, no matter how good its reasoning is in the moment.

## Three kinds of memory

- **Short-term memory**: what's been said in the current conversation.
  It's small on purpose and disappears when the task ends.
- **Long-term memory**: stable facts about a user or situation, saved
  to disk so they survive across sessions. A preferred contact method
  or a known account ID belongs here.
- **Episodic memory**: a log of what actually happened, in order. Not
  a fact like "prefers email," but an event like "a refund was
  requested for order ORD-1001 on this date." Episodic memory answers
  "what happened last time," not just "what do we know."

## Why memory makes agents feel personal and useful

Think of a good receptionist: they remember your name, your usual
order, and what you talked about last time, without you repeating
yourself. That's not a trick, it's just memory applied well. An agent
that recalls a fact it was told once, or a request it already
handled, feels like it's actually paying attention, which is the
difference between a tool you tolerate and one you trust.

## The tradeoff

Memory isn't free. More long-term facts and more episodes mean more
context to fit into a prompt, more decisions about what's actually
relevant right now, and more things that can quietly go stale. A fact
remembered from six months ago might not be true anymore. The goal
isn't to remember everything, it's to remember the right things and
know when to double-check them.

## What we're building today

A memory layer the Day 15 agent can read from and write to:

- `short_term_memory.py`, a bounded window of the current conversation
- `long_term_memory.py`, key-value facts persisted to a JSON file
- `episodic_memory.py`, a timestamped log of past events
- `memory_retrieval.py`, picking the few relevant memories instead of dumping all of them
- `memory_update_rules.py`, deciding what should and shouldn't be saved
- `agent_with_memory.py`, wiring all three kinds of memory into the Day 15 agent loop
- `memory_staleness.py`, noticing when a remembered fact might no longer be true

## How this connects to RAG

Memory retrieval and document retrieval are the same idea applied to
different material. Days 1 through 14 retrieved the most relevant
chunks of a document collection before generating an answer. Today's
`memory_retrieval.py` does the same thing against a much smaller
collection: the facts and episodes an agent has accumulated about one
user or task. Rank by relevance, keep only what fits the budget, and
leave the rest out, exactly like a RAG pipeline leaves out the
documents that didn't make the cut.
