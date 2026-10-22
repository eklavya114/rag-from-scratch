"""
thought_quality.py

Writing a thought down isn't automatically useful -- a thought can be
weak, bad, or actively misleading. This file shows four kinds of
thoughts (two good, two bad) and a simple checker that flags one
specific, checkable failure: a thought that never engages with the
most recent Observation at all.
"""

import re


def weak_thought_restates_question(question):
    """WEAK: just repeats the question back, with no actual plan attached -- provides no more information than the question itself already did."""
    return f"The question is: {question}"


def good_thought_plans_next_step():
    """GOOD: states a concrete plan for what to do next, and why."""
    return "I should look up the order first, since I can't check refund eligibility without knowing its status."


def bad_thought_ignores_observation(last_observation):
    """BAD: proceeds as if the last observation never happened -- repeats the same plan regardless of what was actually learned."""
    return "I should check refund eligibility now."  # never references last_observation at all


def good_thought_checks_assumption(last_observation):
    """GOOD: explicitly reacts to what the last observation actually said, including questioning an assumption it might have falsified."""
    status = last_observation.get("status", "unknown")
    return f"The last observation showed status '{status}' -- I should confirm that's 'delivered' before assuming a refund question even applies."


def extract_significant_words(text):
    """Pulls out words worth checking for overlap -- skips short/common words so the check isn't fooled by trivial overlaps like 'the' or 'a'."""
    stopwords = {"the", "a", "an", "is", "it", "to", "of", "and", "i", "should", "now"}
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in stopwords and len(w) > 2}


def thought_ignores_last_observation(thought, last_observation):
    """
    A SIMPLE CHECKER: flags a thought that shares no significant
    vocabulary at all with the last observation. This is a heuristic,
    not a proof of reasoning quality -- a thought CAN legitimately
    reference an observation without reusing its exact words -- but a
    complete absence of any shared vocabulary is a reasonable signal
    that the observation was never actually considered.
    """
    if last_observation is None:
        return False  # nothing to ignore yet -- this is the first step

    observation_words = extract_significant_words(str(last_observation))
    thought_words = extract_significant_words(thought)
    overlap = observation_words & thought_words
    return len(overlap) == 0


def main():
    print("=== What Makes a Thought Useful ===\n")

    last_observation = {"status": "shipped", "order_id": "ORD-1002"}

    examples = [
        ("Weak (restates the question)", weak_thought_restates_question("Is this order eligible for a refund?"), None),
        ("Good (plans the next step)", good_thought_plans_next_step(), None),
        ("Bad (ignores the last observation)", bad_thought_ignores_observation(last_observation), last_observation),
        ("Good (checks an assumption)", good_thought_checks_assumption(last_observation), last_observation),
    ]

    for label, thought, observation in examples:
        print(f"--- {label} ---")
        print(f"Thought: {thought}")
        if observation is not None:
            flagged = thought_ignores_last_observation(thought, observation)
            verdict = "FLAGGED: appears to ignore the last observation" if flagged else "OK: engages with the last observation"
            print(f"Checker: {verdict}")
        else:
            print("Checker: (no prior observation to check against yet)")
        print()

    print(
        "Why this matters: a thought that merely restates the question "
        "wastes a reasoning step without adding a plan; a thought that "
        "ignores what was just observed defeats the entire point of ReAct, "
        "since the whole value of the pattern is reacting to what actually "
        "happened, not what was expected to happen. A simple vocabulary-"
        "overlap check like this one won't catch every bad thought, but it "
        "catches the cheapest and most common failure: a thought that was "
        "never actually updated by the observation it followed."
    )


if __name__ == "__main__":
    main()
