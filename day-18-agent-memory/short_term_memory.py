"""
short_term_memory.py

Short-term memory holds the current conversation, and only the current
conversation. It has a size limit on purpose: an unbounded conversation
history eventually stops fitting in a prompt, and most of it stops
being relevant anyway as a task moves on. This class keeps only the
last N messages and drops the rest.
"""

from collections import deque


class ShortTermMemory:
    """Stores the last N messages for the current task. Oldest messages are dropped automatically once the limit is reached, using a deque for O(1) drops instead of manually slicing a list."""

    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)

    def add(self, role, content):
        """Adds one message to the window. If the window is already full, the oldest message is silently dropped to make room."""
        self.messages.append({"role": role, "content": content})

    def as_text(self):
        """Formats the current window as plain text, the shape it would actually be inserted into a prompt."""
        if not self.messages:
            return "(no conversation yet)"
        lines = [f"{m['role']}: {m['content']}" for m in self.messages]
        return "\n".join(lines)

    def __len__(self):
        return len(self.messages)


def main():
    print("=== Short-Term Memory ===\n")

    memory = ShortTermMemory(max_messages=4)

    conversation = [
        ("user", "What is RAG?"),
        ("agent", "Retrieval-Augmented Generation. It retrieves documents before generating an answer."),
        ("user", "Does it need a vector database?"),
        ("agent", "Not strictly, but it usually helps for larger document sets."),
        ("user", "What about caching?"),
        ("agent", "Caching can skip repeated retrieval and generation work entirely."),
    ]

    print(f"Memory limit: {memory.max_messages} messages\n")
    for role, content in conversation:
        memory.add(role, content)
        print(f"Added ({role}): {content}")

    print(f"\nTotal messages sent: {len(conversation)}")
    print(f"Messages retained: {len(memory)}\n")

    print("--- What the prompt would actually see ---\n")
    print(memory.as_text())

    print(
        "\nWhy the size limit matters: a conversation that keeps growing "
        "without bound eventually stops fitting in a prompt at all, and "
        "even before that point, most of a long conversation has stopped "
        "being relevant to the current step. Dropping the oldest messages "
        "keeps the window small and keeps it focused on what's actually "
        "recent, at the cost of being unable to recall something said much "
        "earlier, which is exactly the gap long-term and episodic memory "
        "exist to fill."
    )


if __name__ == "__main__":
    main()
