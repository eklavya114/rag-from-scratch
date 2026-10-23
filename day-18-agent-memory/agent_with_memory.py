"""
agent_with_memory.py

Wires all three kinds of memory into the Day 15 agent loop shape:
before a task, load relevant long-term facts and recent episodes into
context; after a task, record an episode and save any new stable
facts. Run two separate sessions (two fresh sets of in-memory objects,
loading from the same files on disk) to show a fact learned in session
one being used in session two without being told again. The "LLM" is
scripted, the same convention as every agent script since Day 15.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))

from long_term_memory import LongTermMemory
from episodic_memory import EpisodicMemory
from memory_update_rules import update_fact
from short_term_memory import ShortTermMemory

FACTS_PATH = os.path.join(os.path.dirname(__file__), "agent_long_term_memory.json")
EPISODES_PATH = os.path.join(os.path.dirname(__file__), "agent_episodic_memory.json")


def fake_llm_session_one(short_term):
    """SESSION 1: the user states a preference. The agent notices it's a stable fact worth saving."""
    short_term.add("user", "I'd like you to reach me by email from now on.")
    return {"learned_fact": ("preferred_contact_method", "email"), "response": "Got it, I'll use email going forward."}


def fake_llm_session_two(short_term, known_facts):
    """SESSION 2: a brand new conversation. The agent is never told the contact preference again, but uses it anyway because it was loaded from long-term memory before this turn started."""
    short_term.add("user", "Please let me know when my refund is processed.")
    contact_method = known_facts.get("preferred_contact_method", "a default channel")
    return {"response": f"I'll notify you by {contact_method} once the refund is processed, as you prefer."}


def run_session(session_label, llm_fn, task_description):
    """
    One full iteration of the memory loop: load relevant long-term
    facts and recent episodes BEFORE the task, run the task, then
    record an episode and save any new stable facts AFTER the task.
    """
    print(f"--- {session_label} ---\n")

    long_term = LongTermMemory(path=FACTS_PATH)
    episodic = EpisodicMemory(path=EPISODES_PATH)
    short_term = ShortTermMemory(max_messages=10)

    # BEFORE the task: load what's already known.
    known_facts = dict(long_term.facts)
    recent_episodes = episodic.recent(limit=3)
    print(f"Loaded {len(known_facts)} known fact(s): {known_facts}")
    print(f"Loaded {len(recent_episodes)} recent episode(s).\n")

    print(f"Task: {task_description}")
    result = llm_fn(short_term, known_facts) if llm_fn is fake_llm_session_two else llm_fn(short_term)
    print(f"Agent response: {result['response']}\n")

    # AFTER the task: record what happened, save any new stable fact.
    episodic.record("task_completed", {"session": session_label, "task": task_description})

    if "learned_fact" in result:
        key, value = result["learned_fact"]
        update_result = update_fact(long_term.facts, key, value)
        if update_result["ok"]:
            long_term._save()
            print(f"Saved new fact: {key} = {value} ({update_result['action']})")

    return result


def main():
    print("=== Agent With Memory, Across Two Sessions ===\n")

    # Start from a clean slate so this demo is reproducible on every run.
    for path in (FACTS_PATH, EPISODES_PATH):
        if os.path.exists(path):
            os.remove(path)

    run_session(
        "Session 1 (learns the user prefers email)",
        fake_llm_session_one,
        "User mentions they'd like to be contacted by email.",
    )

    run_session(
        "Session 2 (a new process, fact recalled without being retold)",
        fake_llm_session_two,
        "User asks to be notified when a refund is processed.",
    )

    print("=== Why this worked ===\n")
    print(
        "Session 2 never received the word 'email' anywhere in its own "
        "conversation. It knew to use email only because session 1's "
        "LongTermMemory instance saved that fact to disk, and session 2's "
        "LongTermMemory instance (a completely separate object, as a new "
        "process would create) loaded it back before the task started. "
        "That load-before, save-after shape is the entire memory loop: "
        "everything else in this folder exists to decide WHAT belongs in "
        "that load and that save."
    )

    for path in (FACTS_PATH, EPISODES_PATH):
        if os.path.exists(path):
            os.remove(path)
    print(f"\nCleaned up memory files.")


if __name__ == "__main__":
    main()
