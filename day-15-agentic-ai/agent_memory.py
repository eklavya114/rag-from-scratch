"""
agent_memory.py

Every agent so far forgets everything the moment it finishes a run.
Real agents benefit from two kinds of memory: short-term (what's
happening in THIS task) and long-term (what was learned across PAST
tasks, persisted to disk so it survives between runs). This file shows
both, including an agent that actually answers faster/better on its
second run because of something it remembered from its first.
"""

import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "long_term_memory.json")


class ShortTermMemory:
    """CURRENT TASK CONTEXT: holds only what's relevant to the task in progress. Cleared between tasks -- it isn't meant to persist."""

    def __init__(self):
        self.entries = []

    def add(self, entry):
        self.entries.append(entry)

    def recent(self, n=3):
        return self.entries[-n:]

    def clear(self):
        self.entries = []


class LongTermMemory:
    """
    PAST LEARNINGS: persisted to a JSON file so facts learned in one
    run are available in later runs, not just later steps of the same
    run. This is what lets an agent get faster/smarter over multiple
    sessions instead of starting from zero every time.
    """

    def __init__(self, path=MEMORY_FILE):
        self.path = path
        self.facts = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.facts, f, indent=2)

    def remember(self, key, value):
        """MEMORY UPDATE: learn something new and persist it immediately, so a crash right after doesn't lose the fact."""
        self.facts[key] = value
        self._save()

    def recall(self, key):
        """MEMORY RETRIEVAL: look up something previously learned, returning None if it was never stored."""
        return self.facts.get(key)


def agent_answer_question(question, short_term, long_term, tool_call_log):
    """
    Simulates an agent answering a question, checking long-term memory
    FIRST (cheap, instant) before falling back to a "tool call" (slow,
    simulated here by just appending to a log so the cost is visible).
    """
    short_term.add({"question": question})

    cached = long_term.recall(question)
    if cached is not None:
        short_term.add({"source": "long_term_memory", "answer": cached})
        return cached, "memory_hit"

    # Not remembered yet -- fall back to the "search tool" (an expensive call we want to avoid repeating).
    tool_call_log.append(question)
    answer = f"The answer to '{question}' is 42 (computed via tool call)."
    long_term.remember(question, answer)
    short_term.add({"source": "tool_call", "answer": answer})
    return answer, "tool_call"


def main():
    print("=== Agent Memory ===\n")

    # Start with a clean slate so this demo is reproducible on every run.
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

    short_term = ShortTermMemory()
    long_term = LongTermMemory()
    tool_call_log = []

    question = "What is the meaning of life?"

    print("--- First time asking this question ---")
    answer, path = agent_answer_question(question, short_term, long_term, tool_call_log)
    print(f"Answer: {answer}")
    print(f"Path: {path}")
    print(f"Tool calls made so far: {len(tool_call_log)}\n")

    print("--- Asking the SAME question again (new short-term context, same long-term memory) ---")
    short_term.clear()  # simulates a brand new task/session -- short-term memory does NOT carry over
    answer, path = agent_answer_question(question, short_term, long_term, tool_call_log)
    print(f"Answer: {answer}")
    print(f"Path: {path}")
    print(f"Tool calls made so far: {len(tool_call_log)}")

    print(
        f"\nThe second call reused the remembered answer instead of "
        f"calling the tool again -- {len(tool_call_log)} real tool call(s) "
        f"total for 2 questions, because long-term memory persisted across "
        f"the 'new session' (short_term.clear()) while long_term did not."
    )

    print("\n--- Short-term memory for the current task ---")
    for entry in short_term.recent():
        print(f"  {entry}")

    print(f"\nLong-term memory file: {long_term.path}")
    print(f"Facts remembered: {list(long_term.facts.keys())}")


if __name__ == "__main__":
    main()
