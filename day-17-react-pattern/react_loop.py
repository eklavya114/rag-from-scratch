"""
react_loop.py

The full ReAct loop: ask the "LLM" for the next Thought/Action/Action
Input (or Final Answer), parse it, run the matching tool from Day 15's
ToolRegistry, feed the Observation back in, and repeat -- printing the
full trace as it happens. The "LLM" is a small scripted function so
this runs without any API key, the same convention as Day 15 and 16.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from tool_registry import ToolRegistry  # Day 15
from tool_builder import build_tool_from_function  # Day 16
from support_tools import check_refund_eligibility, lookup_order  # Day 16

from react_parser import parse_react_text


def fake_llm_react_step(question, history, step_number):
    """
    STAND-IN FOR A REAL LLM: given the question and the history of
    (thought, action, observation) so far, produces the next turn as
    ReAct-formatted text. A real LLM would generate this from the
    question and the growing transcript; here it's scripted so the
    loop is deterministic and needs no API key.
    """
    if step_number == 1:
        return "Thought: I need to look up the order before I can say anything about a refund.\nAction: lookup_order\nAction Input: ORD-1003"

    if step_number == 2:
        last_observation = history[-1]["observation"]
        if last_observation.get("status") == "delivered":
            return "Thought: The order has been delivered, so now I should check whether it's still within the refund window.\nAction: check_refund_eligibility\nAction Input: ORD-1003"
        return "Thought: The order hasn't been delivered yet, so a refund question doesn't apply the same way.\nFinal Answer: This order hasn't been delivered yet, so refund eligibility doesn't apply."

    if step_number == 3:
        last_observation = history[-1]["observation"]
        if last_observation.get("eligible"):
            return "Thought: I have a clear, grounded answer now.\nFinal Answer: Yes, this order is eligible for a refund."
        return f"Thought: I have a clear, grounded answer now.\nFinal Answer: No, this order is not eligible for a refund ({last_observation.get('reason')})."

    return "Thought: I should wrap up.\nFinal Answer: Unable to determine a final answer within the step budget."


class ReActAgent:
    """Runs the Thought/Action/Observation loop until a Final Answer appears or max_steps is reached."""

    def __init__(self, registry, max_steps=6):
        self.registry = registry
        self.max_steps = max_steps
        self.history = []  # list of {"thought": str, "action": str, "action_input": str, "observation": ...}

    def run(self, question):
        print(f"Question: {question}\n")

        for step_number in range(1, self.max_steps + 1):
            raw_text = fake_llm_react_step(question, self.history, step_number)
            parsed = parse_react_text(raw_text)

            print(f"Thought: {parsed.thought}")

            if parsed.final_answer:
                print(f"Final Answer: {parsed.final_answer}\n")
                return parsed.final_answer

            if parsed.action not in self.registry.list_tool_names():
                print(f"Action '{parsed.action}' is not a registered tool -- stopping.")
                return None

            print(f"Action: {parsed.action}")
            print(f"Action Input: {parsed.action_input}")

            observation = self.registry.call(parsed.action, parsed.action_input)
            print(f"Observation: {observation}\n")

            self.history.append({
                "thought": parsed.thought,
                "action": parsed.action,
                "action_input": parsed.action_input,
                "observation": observation,
            })

        print(f"Stopped after reaching the {self.max_steps}-step limit without a Final Answer.\n")
        return None


def main():
    print("=== The ReAct Loop ===\n")

    registry = ToolRegistry()
    for function in (lookup_order, check_refund_eligibility):
        build_tool_from_function(registry, function)

    agent = ReActAgent(registry)
    answer = agent.run("Is order ORD-1003 eligible for a refund?")

    print(f"Total reasoning steps taken: {len(agent.history)}")
    print(f"Final answer returned: {answer}")


if __name__ == "__main__":
    main()
