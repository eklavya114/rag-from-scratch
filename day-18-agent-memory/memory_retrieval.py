"""
memory_retrieval.py

Having memory isn't the same as using it well. This file shows the
three ways an agent might recall something (exact key, keyword match,
recency), then ranks everything it found by relevance to the current
task, and keeps only a small budget of the best matches, the same
retrieve-then-rank-then-limit shape used for document retrieval all the
way back on Day 6.
"""

import re


def recall_by_exact_key(facts, key):
    """EXACT KEY RECALL: the cheapest and most reliable form, when the agent already knows exactly which fact it wants."""
    return facts.get(key)


def recall_by_keyword(facts, query):
    """
    KEYWORD RECALL: scans stored facts for ones whose key or value
    shares a word with the query, for when the agent doesn't know the
    exact key to ask for but has a general sense of what it's looking
    for.
    """
    query_words = extract_words(query)
    matches = []
    for key, value in facts.items():
        fact_words = extract_words(key) | extract_words(str(value))
        if query_words & fact_words:
            matches.append((key, value))
    return matches


def recall_by_recency(episodes, limit=5):
    """RECENCY RECALL: the most recent episodes, regardless of their content, for "what happened lately" style questions."""
    return list(reversed(episodes))[:limit]


def extract_words(text):
    """Pulls out lowercase words worth matching on, skipping very short ones that would create meaningless overlaps."""
    return {w for w in re.findall(r"[a-zA-Z]+", text.lower()) if len(w) > 2}


def score_relevance(task, memory_text):
    """
    Scores one memory's relevance to the current task using simple
    word overlap, the same idea as similarity scoring everywhere else
    in this project, just applied to memory text instead of document
    chunks.
    """
    task_words = extract_words(task)
    memory_words = extract_words(memory_text)
    if not task_words or not memory_words:
        return 0.0
    overlap = task_words & memory_words
    return len(overlap) / len(task_words)


def rank_and_limit_memories(task, candidate_memories, budget=3):
    """
    RANK BY RELEVANCE, THEN LIMIT: scores every candidate memory
    against the current task, sorts by score, and keeps only the top
    `budget` entries, the same way a RAG pipeline keeps only its
    top-k retrieved chunks instead of the entire document collection.
    """
    scored = [(memory_text, score_relevance(task, memory_text)) for memory_text in candidate_memories]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:budget]


def main():
    print("=== Memory Retrieval ===\n")

    facts = {
        "preferred_contact_method": "email",
        "account_id": "CUST-42",
        "favorite_product": "Wireless Mouse",
        "signup_year": 2024,
    }

    episodes = [
        {"event_type": "refund_requested", "details": {"order_id": "ORD-1001"}},
        {"event_type": "ticket_created", "details": {"issue": "late delivery"}},
        {"event_type": "refund_requested", "details": {"order_id": "ORD-1002"}},
    ]

    print("--- Recall by exact key ---")
    print(f"preferred_contact_method -> {recall_by_exact_key(facts, 'preferred_contact_method')}")

    print("\n--- Recall by keyword ---")
    query = "What is this customer's favorite product?"
    matches = recall_by_keyword(facts, query)
    print(f"Query: '{query}' -> {matches}")

    print("\n--- Recall by recency ---")
    for episode in recall_by_recency(episodes, limit=2):
        print(f"  {episode}")

    print("\n--- Ranking candidate memories against a task, then applying a budget ---")
    task = "Help the customer with a refund for their order"
    candidates = [
        f"{key}: {value}" for key, value in facts.items()
    ] + [
        f"{e['event_type']}: {e['details']}" for e in episodes
    ]

    print(f"Task: '{task}'")
    print(f"Candidate memories available: {len(candidates)}\n")

    ranked = rank_and_limit_memories(task, candidates, budget=3)
    print("Top 3 memories selected for this task:")
    for memory_text, score in ranked:
        print(f"  score={score:.2f}  {memory_text}")

    print(
        "\nWhy retrieving fewer, better memories beats dumping everything: "
        "every fact and episode included in a prompt costs context space "
        "and competes for the model's attention. A handful of memories "
        "that are actually relevant to the task at hand are more useful "
        "than every memory ever recorded, most of which has nothing to do "
        "with the question being asked right now."
    )


if __name__ == "__main__":
    main()
