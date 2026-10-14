# Day 15 Best Practices: Building Agents

## Keep tools small

`tool_examples.py` gives each tool exactly one job (search, calculate,
send an email, create a ticket). A tool that does three things is
harder for an LLM to decide when to call and harder for a human to
debug when it misbehaves. One tool, one responsibility, one clear
return shape.

## Limit steps

Every agent loop in this folder (`simple_agent.py`, `error_handling.py`)
has a hard `max_steps` ceiling. Without one, a bad decision function or
a confused LLM can loop forever, burning time and (with a real API)
real money. A step limit turns "runs forever" into "fails loudly and
stops," which is always the better failure mode.

## Log every action

`agent_reasoning.py` records a full think/decide/act/observe trace, and
`agent_memory.py` and `multi_step_tasks.py` print every tool call as it
happens. An agent that doesn't log what it did and why is nearly
impossible to debug after the fact -- "it didn't work" needs to become
"step 3 called the wrong tool with these arguments," and that only
works if the trace was captured.

## Never trust tool output blindly

`error_handling.py`'s `unpredictable_lookup` demo and `call_tool_safely`
wrapper both exist for this reason: a tool can return `None`, an error
string, or something in an unexpected shape without ever raising an
exception. Check what a tool actually returned before acting on it --
"the call succeeded" and "the result is usable" are different claims.

## Design for failure, not just the happy path

`multi_step_tasks.py` showed a step failing on its first attempt and
succeeding on a retry; `error_handling.py` showed a fallback kicking in
when a primary tool was unreachable entirely. Assume any given tool
call can fail, and decide ahead of time whether the right response is
retry, fallback, or stop the whole task -- don't let that decision
happen by accident at runtime.

## Measure, don't eyeball

`agent_evaluation.py` turned "the agent seems to work" into concrete
numbers: completion rate, average steps, tool error rate. Without
those numbers, there's no way to tell whether a change to an agent's
prompt or tools made it better or worse -- only whether it still
*looks* fine on the one example you happened to try.

## Memory should be scoped, not global

`agent_memory.py`'s short-term memory is cleared between tasks on
purpose; its long-term memory persists to disk on purpose. Mixing the
two -- carrying this task's scratch context into the next task, or
never persisting a genuinely reusable fact -- produces an agent that
either forgets things it shouldn't or remembers things it shouldn't,
both of which erode trust in its answers over time.

## RAG and agents are complementary, not competing

`integration_with_previous_days.py` showed the real difference directly:
a guess-only tool with no access to real documents produced a vague,
ungrounded answer, while the same question through the real Day 5/6/7
RAG pipeline came back grounded in actual indexed text. An agent's
reasoning is only as good as what it has access to -- give it RAG as a
tool rather than asking it to work from a model's memorized guesses.
