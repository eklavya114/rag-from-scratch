"""
episodic_memory.py

Long-term memory stores facts: "prefers email." Episodic memory stores
events: "a refund was requested for order ORD-1001 on this date." The
difference matters: a fact says what is true right now, an episode says
what actually happened, in order, so an agent can answer questions like
"what did we already try" or "when did this last come up."
"""

import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "episodic_memory.json")


class EpisodicMemory:
    """A timestamped log of past events. A good episode records what happened, when, and enough detail to act on later, without trying to also hold a running summary or a judgment about it."""

    def __init__(self, path=None):
        self.path = path
        self.episodes = self._load() if path else []
        self._next_timestamp = 1000  # a simple incrementing counter standing in for real wall-clock time, so this demo is reproducible

    def _load(self):
        if self.path and os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        if self.path:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.episodes, f, indent=2)

    def record(self, event_type, details):
        """Records one event with a type and a details dict. The timestamp is assigned automatically, in the order episodes are recorded."""
        episode = {
            "timestamp": self._next_timestamp,
            "event_type": event_type,
            "details": details,
        }
        self._next_timestamp += 1
        self.episodes.append(episode)
        self._save()
        return episode

    def recent(self, event_type=None, limit=5):
        """Returns the most recent episodes, optionally filtered to one event_type, most recent first."""
        matching = [e for e in self.episodes if event_type is None or e["event_type"] == event_type]
        return list(reversed(matching))[:limit]

    def find_by_detail(self, event_type, detail_key, detail_value):
        """Finds episodes of a given type where a specific detail field matches a given value, most recent first. This is how 'the last refund request for order 1001' actually gets answered."""
        matches = [
            e for e in self.episodes
            if e["event_type"] == event_type and e["details"].get(detail_key) == detail_value
        ]
        return list(reversed(matches))


def main():
    print("=== Episodic Memory ===\n")

    memory = EpisodicMemory()

    memory.record("refund_requested", {"order_id": "ORD-1001", "amount": 25.00})
    memory.record("ticket_created", {"ticket_id": "TICKET-1001", "issue": "late delivery"})
    memory.record("refund_requested", {"order_id": "ORD-1002", "amount": 89.00})
    memory.record("refund_requested", {"order_id": "ORD-1001", "amount": 25.00, "note": "customer followed up"})
    memory.record("ticket_created", {"ticket_id": "TICKET-1002", "issue": "damaged item"})

    print(f"Total episodes recorded: {len(memory.episodes)}\n")

    print("--- Most recent 3 episodes, any type ---")
    for episode in memory.recent(limit=3):
        print(f"  [{episode['timestamp']}] {episode['event_type']}: {episode['details']}")

    print("\n--- Most recent refund_requested episodes ---")
    for episode in memory.recent(event_type="refund_requested", limit=5):
        print(f"  [{episode['timestamp']}] {episode['details']}")

    print("\n--- Looking up: the last refund request for order ORD-1001 ---")
    matches = memory.find_by_detail("refund_requested", "order_id", "ORD-1001")
    if matches:
        latest = matches[0]
        print(f"Found {len(matches)} matching episode(s). Most recent: [{latest['timestamp']}] {latest['details']}")
    else:
        print("No matching episodes found.")

    print(
        "\nWhat makes a good episode: a clear event_type, a timestamp (or "
        "ordering), and just enough structured detail to act on later, "
        "same discipline as a well-designed tool result from Day 16. An "
        "episode that's just a vague text blob is as hard for an agent to "
        "use later as the messy, unstructured tool outputs Day 16 warned "
        "against."
    )


if __name__ == "__main__":
    main()
