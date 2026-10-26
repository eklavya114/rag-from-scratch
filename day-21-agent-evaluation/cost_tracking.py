"""
cost_tracking.py

Estimates a rough cost per run, in dollars, using a simple word-count
estimate of tokens instead of a real tokenizer. The goal here is not
billing-grade accuracy, it is to show that cost tracking exists at all
and that it can reveal an agent that is wasteful without being any more
correct. The price below is a clearly labeled EXAMPLE price, not a real
rate from any provider.

Important: this file does not call any real API or import any vendor
SDK. It only estimates what a real run would cost, using word counts.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval_tasks import TEST_SET
from graders import grade_run
from scripted_agents import AGENTS

# EXAMPLE price only, not a real rate from any provider.
EXAMPLE_PRICE_PER_1000_TOKENS = 0.01

# A rough estimate: 1 word is roughly 1.3 tokens for English text. This is
# a common rule of thumb, not an exact conversion, and is good enough for
# comparing agents against each other, which is all we need it for here.
WORDS_TO_TOKENS = 1.3


def estimate_tokens(text):
    """A simple word-count-based token estimate. No real tokenizer involved."""
    word_count = len(str(text).split())
    return int(word_count * WORDS_TO_TOKENS)


def estimate_run_cost(run, goal):
    """
    Estimates the token cost of one run: the goal text is sent once as
    the prompt, and then every tool call's arguments and result get
    added back into the conversation as the agent reads what happened,
    plus the final answer the agent produces. More tool calls means more
    text going back and forth, which means more estimated tokens.
    """
    total_tokens = estimate_tokens(goal)
    for call in run["tool_calls"]:
        total_tokens += estimate_tokens(call["args"])
        total_tokens += estimate_tokens(call["result"])
    total_tokens += estimate_tokens(run["final_answer"])

    cost = (total_tokens / 1000) * EXAMPLE_PRICE_PER_1000_TOKENS
    return total_tokens, cost


def main():
    print("=== Cost Tracking ===\n")
    print(f"Example price used: ${EXAMPLE_PRICE_PER_1000_TOKENS} per 1000 tokens (illustrative, not a real rate)\n")

    for agent_name, agent_fn in AGENTS.items():
        print(f"--- {agent_name} agent ---")
        total_cost = 0.0
        successful_cost = 0.0
        successful_count = 0

        for task in TEST_SET:
            run = agent_fn(task)
            grade = grade_run(run, task, agent_name)
            tokens, cost = estimate_run_cost(run, task.goal)
            total_cost += cost
            if grade.task_success and not grade.forbidden_call_made:
                successful_cost += cost
                successful_count += 1
            print(f"  {task.task_id:<28} tokens={tokens:<5} cost=${cost:.5f}")

        cost_per_task = total_cost / len(TEST_SET)
        cost_per_success = successful_cost / successful_count if successful_count else float("inf")

        print(f"  Total cost:              ${total_cost:.5f}")
        print(f"  Cost per task:           ${cost_per_task:.5f}")
        print(f"  Cost per successful task:${cost_per_success:.5f}")
        print()

    print(
        "Why cost per success matters more than cost per call: the sloppy "
        "agent makes one extra tool call on every task, which raises its "
        "total cost, without raising how many tasks it actually completes "
        "correctly. Looking only at total cost or cost per call would make "
        "sloppy look like it is doing proportionally more work. Dividing "
        "cost by the number of actually successful runs is what reveals "
        "that the extra spending bought nothing."
    )


if __name__ == "__main__":
    main()
