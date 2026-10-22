"""
react_parser.py

Parses the ReAct text format described in README.md: lines starting
with "Thought:", "Action:", "Action Input:", and "Final Answer:". A
real LLM produces this as free text; an agent needs to turn that text
back into something it can act on. This parser does exactly that, and
fails with a clear, specific error message when the text is malformed
rather than silently guessing.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReActStep:
    """A single parsed ReAct step. Exactly one of (action + action_input) or final_answer should be set -- never both, never neither."""
    thought: Optional[str] = None
    action: Optional[str] = None
    action_input: Optional[str] = None
    final_answer: Optional[str] = None


class ReActParseError(ValueError):
    """Raised when ReAct-formatted text is malformed in a way the parser can't recover from."""


def parse_react_text(text):
    """
    Parses one ReAct "turn" of text into a ReActStep. Recognizes four
    line prefixes (case-sensitive, matching the format in README.md):
    "Thought:", "Action:", "Action Input:", and "Final Answer:". Any
    other line is ignored, so minor formatting noise doesn't break
    parsing.
    """
    thought = None
    action = None
    action_input = None
    final_answer = None

    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("Thought:"):
            thought = line[len("Thought:"):].strip()
        elif line.startswith("Action Input:"):
            action_input = line[len("Action Input:"):].strip()
        elif line.startswith("Action:"):
            action = line[len("Action:"):].strip()
        elif line.startswith("Final Answer:"):
            final_answer = line[len("Final Answer:"):].strip()

    # VALIDATE: an Action with no Action Input is malformed -- the tool can't be called without arguments.
    if action and not action_input:
        raise ReActParseError(f"Found Action '{action}' but no matching Action Input line.")

    # VALIDATE: a turn must propose EITHER an action OR a final answer, not neither.
    if not action and not final_answer:
        raise ReActParseError("Found neither an Action nor a Final Answer -- nothing for the agent to do with this turn.")

    # VALIDATE: a turn must propose EITHER an action OR a final answer, not both -- ambiguous which one to follow.
    if action and final_answer:
        raise ReActParseError("Found both an Action and a Final Answer in the same turn -- only one is allowed.")

    return ReActStep(thought=thought, action=action, action_input=action_input, final_answer=final_answer)


def main():
    print("=== Parsing ReAct Text ===\n")

    good_examples = [
        "Thought: I need to look up the order first.\nAction: lookup_order\nAction Input: ORD-1001",
        "Thought: I now have enough information.\nFinal Answer: Yes, the order is eligible.",
        "Thought: Let me check the refund rule.\nAction: check_refund_eligibility\nAction Input: ORD-1003\n",
    ]

    print("--- Well-formed examples ---\n")
    for i, text in enumerate(good_examples, start=1):
        step = parse_react_text(text)
        print(f"Example {i}:")
        print(f"  input: {text!r}")
        print(f"  parsed: {step}\n")

    broken_examples = [
        "Thought: I should look something up.\nAction: lookup_order",  # action with no action input
        "Thought: Hmm, not sure what to do.",  # no action AND no final answer
    ]

    print("--- Malformed examples (clear errors expected) ---\n")
    for i, text in enumerate(broken_examples, start=1):
        print(f"Broken example {i}:")
        print(f"  input: {text!r}")
        try:
            parse_react_text(text)
            print("  parsed WITHOUT error (unexpected!)")
        except ReActParseError as exc:
            print(f"  correctly rejected: {exc}\n")


if __name__ == "__main__":
    main()
