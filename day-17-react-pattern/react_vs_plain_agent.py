"""
react_vs_plain_agent.py

Same task, same tools, two agents: a "plain" agent that acts without
writing down any reasoning (scripted to make a wrong early guess and
then never reconsider it), and a ReAct agent (scripted to notice the
same bad assumption from its Observation and correct course). Running
both side by side on one task makes the benefit of a visible thought
concrete instead of asserted.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from tool_registry import ToolRegistry  # Day 15
from tool_builder import build_tool_from_function  # Day 16
from support_tools import check_refund_eligibility, lookup_order  # Day 16

from react_parser import parse_react_text

TASK = "Is order ORD-1002 eligible for a refund?"
# ORD-1002 is still "shipped", not yet "delivered" -- the trap both agents are tested against.


def run_plain_agent(registry):
    """
    PLAIN AGENT: picks an action and executes it with no written
    reasoning step. Scripted here to assume refund-eligibility can be
    checked directly without first confirming delivery status -- a
    wrong assumption that nothing in this agent's design surfaces or
    reconsiders, because there's no thought step to catch it in.
    """
    print("--- Plain agent (no visible reasoning) ---\n")

    action, action_input = "check_refund_eligibility", "ORD-1002"
    print(f"Action: {action}({action_input!r})")
    result = registry.call(action, action_input)
    print(f"Result: {result}")

    # The plain agent has no mechanism to notice that result doesn't actually answer
    # the real-world question ("is a refund even relevant yet?") -- it just reports it.
    print(f"\nAnswer given: {'Eligible' if result.get('eligible') else 'Not eligible'} for a refund.")
    print("(No check was ever made on whether the order has even been delivered.)\n")
    return result


def fake_llm_react_step(history, step_number):
    """Scripted ReAct turns for this specific task -- checks delivery status FIRST, because the thought step surfaces that as something worth verifying before the real question can be answered."""
    if step_number == 1:
        return "Thought: Before checking refund eligibility, I should confirm the order has actually been delivered -- a refund question may not even apply yet.\nAction: lookup_order\nAction Input: ORD-1002"

    if step_number == 2:
        last_observation = history[-1]["observation"]
        if last_observation.get("status") != "delivered":
            return f"Thought: The observation shows status is '{last_observation.get('status')}', not 'delivered' -- checking refund eligibility now would answer the wrong question.\nFinal Answer: This order hasn't been delivered yet (status: {last_observation.get('status')}), so refund eligibility doesn't apply."
        return "Thought: The order was delivered, so now I can check refund eligibility.\nAction: check_refund_eligibility\nAction Input: ORD-1002"

    return "Thought: Wrapping up.\nFinal Answer: Unable to reach a confident answer."


def run_react_agent(registry, max_steps=4):
    """REACT AGENT: writes a thought before every action. The thought in step 1 explicitly questions the assumption the plain agent made silently -- and step 2's thought catches the surprising observation (status isn't 'delivered') instead of plowing ahead."""
    print("--- ReAct agent (visible reasoning) ---\n")

    history = []
    for step_number in range(1, max_steps + 1):
        raw_text = fake_llm_react_step(history, step_number)
        parsed = parse_react_text(raw_text)

        print(f"Thought: {parsed.thought}")

        if parsed.final_answer:
            print(f"Final Answer: {parsed.final_answer}\n")
            return parsed.final_answer

        print(f"Action: {parsed.action}")
        print(f"Action Input: {parsed.action_input}")
        observation = registry.call(parsed.action, parsed.action_input)
        print(f"Observation: {observation}\n")
        history.append({"thought": parsed.thought, "action": parsed.action, "observation": observation})

    return None


def main():
    print("=== ReAct vs. Plain Agent ===\n")
    print(f"Task: {TASK}\n")

    registry = ToolRegistry()
    for function in (lookup_order, check_refund_eligibility):
        build_tool_from_function(registry, function)

    plain_result = run_plain_agent(registry)
    react_answer = run_react_agent(registry)

    plain_summary = "Eligible" if plain_result.get("eligible") else "Not eligible"

    print("=== Comparison ===\n")
    print(f"Plain agent's answer:  '{plain_summary} for a refund' (the tool call itself ran fine, but the question doesn't make sense yet -- the order hasn't even been delivered)")
    print(f"ReAct agent's answer:  '{react_answer}'")
    print(
        "\nThe plain agent's tool CALL wasn't wrong -- check_refund_eligibility ran "
        "fine and returned a real result. The mistake is upstream: it never asked "
        "whether that was even the right question to ask first. The ReAct agent's "
        "written thought in step 1 made that assumption explicit ('I should confirm "
        "delivery first'), and its step 2 thought caught the surprising observation "
        "(status wasn't 'delivered') before committing to an answer -- exactly the "
        "kind of self-correction a plain, thought-free action loop has no place to do."
    )


if __name__ == "__main__":
    main()
