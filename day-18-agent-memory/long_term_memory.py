"""
long_term_memory.py

Long-term memory holds stable facts that should survive across
sessions, not just the current conversation. It lives as a JSON file on
disk: load it when a new instance starts, save it after every change,
so a fact learned in one process can be recalled by a completely
separate process later.
"""

import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "long_term_memory.json")


class LongTermMemory:
    """Key-value facts persisted to a JSON file on disk. Loaded once at startup, saved immediately after every change, so a crash right after a write never loses that fact."""

    def __init__(self, path=DEFAULT_PATH):
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
        """Saves or overwrites a fact, then persists immediately."""
        self.facts[key] = value
        self._save()

    def recall(self, key):
        """Looks up a fact by its exact key. Returns None if it was never stored."""
        return self.facts.get(key)

    def forget(self, key):
        """Removes a fact entirely, then persists immediately. Safe to call even if the key was never stored."""
        if key in self.facts:
            del self.facts[key]
            self._save()


def main():
    print("=== Long-Term Memory ===\n")

    # Start from a clean file so this demo is reproducible on every run.
    if os.path.exists(DEFAULT_PATH):
        os.remove(DEFAULT_PATH)

    print(f"Facts are saved to: {DEFAULT_PATH}\n")

    print("--- Session 1: a fresh LongTermMemory instance ---")
    session_one = LongTermMemory()
    session_one.remember("preferred_contact_method", "email")
    session_one.remember("account_id", "CUST-42")
    print("Remembered: preferred_contact_method = email")
    print("Remembered: account_id = CUST-42")

    print("\n--- Session 2: a brand NEW LongTermMemory instance ---")
    session_two = LongTermMemory()
    recalled = session_two.recall("preferred_contact_method")
    print(f"Recalled without being told again: preferred_contact_method = {recalled}")

    print("\n--- Forgetting a fact ---")
    session_two.forget("account_id")
    print(f"After forgetting: account_id = {session_two.recall('account_id')!r}")

    print("\n--- A brand new third instance confirms the forget persisted ---")
    session_three = LongTermMemory()
    print(f"account_id in a fresh instance: {session_three.recall('account_id')!r}")
    print(f"preferred_contact_method still there: {session_three.recall('preferred_contact_method')!r}")

    # Clean up so this folder doesn't accumulate a leftover JSON file between runs.
    os.remove(DEFAULT_PATH)
    print(f"\nCleaned up {DEFAULT_PATH}")


if __name__ == "__main__":
    main()
