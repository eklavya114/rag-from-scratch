"""
abuse_and_cost_limits.py

Protects against abuse and runaway cost, layered on TOP of Day 23's
per-minute rate limit, not replacing it. A per-minute limit stops a
burst from overwhelming the service right now. A per-day BUDGET stops a
key from quietly running up real cost over hours, well below any
per-minute threshold, one request every few seconds, all day, every day,
never trips a rate limit but can still represent a serious, sustained
cost if that key should only ever send a handful of real queries.
"""

import time
from collections import deque

MAX_QUERY_LENGTH = 500
MAX_QUERIES_PER_BATCH = 20
DEFAULT_DAILY_BUDGET = 1000

SCRAPE_WINDOW_SECONDS = 10
SCRAPE_SIMILARITY_THRESHOLD = 3  # 3 or more near-identical queries within the window looks like scraping, not normal use


class DailyBudgetTracker:
    """Tracks how many queries each key has sent since the tracker was created, enforcing a simple daily budget (a real system resets this at midnight; this demo tracks it for the life of one run)."""

    def __init__(self, daily_budget=DEFAULT_DAILY_BUDGET):
        self.daily_budget = daily_budget
        self.counts = {}

    def record_and_check(self, api_key):
        """Records one query against a key's running count, and returns (allowed, reason). Once a key's count exceeds its budget, every further query that day is denied, regardless of how far under the per-minute rate limit it is."""
        count = self.counts.get(api_key, 0) + 1
        self.counts[api_key] = count
        if count > self.daily_budget:
            return False, f"Daily budget of {self.daily_budget} queries exceeded (this would be query {count})."
        return True, f"Query {count} of {self.daily_budget} daily budget."


def validate_query_shape(query, batch_size=1):
    """Rejects a query that is too long, or a batch of queries that is too large, BEFORE any real work happens, the same fail-early principle Day 22's request_validation.py already applied to a single query."""
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query is {len(query)} characters, exceeding the {MAX_QUERY_LENGTH}-character limit."
    if batch_size > MAX_QUERIES_PER_BATCH:
        return False, f"Batch of {batch_size} exceeds the {MAX_QUERIES_PER_BATCH}-query batch limit."
    return True, "ok"


class ScrapeDetector:
    """
    Detects a burst of near-identical queries from one key within a
    short window, a common SCRAPING pattern: a real user asks varied
    questions, a scraper sends the same query (or tiny variations of it)
    repeatedly, trying to pull the whole index out through the API one
    near-duplicate request at a time.
    """

    def __init__(self, window_seconds=SCRAPE_WINDOW_SECONDS, similarity_threshold=SCRAPE_SIMILARITY_THRESHOLD):
        self.window_seconds = window_seconds
        self.similarity_threshold = similarity_threshold
        self.recent_queries = {}  # api_key -> deque of (timestamp, normalized_query)

    def _normalize(self, query):
        return query.strip().lower()

    def record_and_check(self, api_key, query, now=None):
        """Records one query and returns (is_scrape_pattern, recent_duplicate_count). A real system would use the query's actual timestamp; this accepts an explicit 'now' for a fast, deterministic demo."""
        now = now if now is not None else time.perf_counter()
        normalized = self._normalize(query)

        history = self.recent_queries.setdefault(api_key, deque())
        history.append((now, normalized))

        while history and now - history[0][0] > self.window_seconds:
            history.popleft()

        duplicate_count = sum(1 for _, q in history if q == normalized)
        is_scrape_pattern = duplicate_count >= self.similarity_threshold
        return is_scrape_pattern, duplicate_count


def main():
    print("=== Abuse and Cost Limits ===\n")

    print("--- A normal user: varied queries, well under every limit ---")
    budget = DailyBudgetTracker(daily_budget=1000)
    detector = ScrapeDetector()
    normal_queries = ["What is RAG?", "What is a vector database?", "What is Python?"]
    for query in normal_queries:
        allowed, reason = budget.record_and_check("key-normal-user")
        is_scrape, dup_count = detector.record_and_check("key-normal-user", query, now=0.0)
        print(f"  {query!r}: budget_allowed={allowed}, scrape_pattern={is_scrape} (dup_count={dup_count})")
    print()

    print("--- A scraper: the same query sent repeatedly in a tight window ---")
    for i in range(5):
        is_scrape, dup_count = detector.record_and_check("key-scraper", "List all documents", now=i * 0.5)
        print(f"  attempt {i + 1}: scrape_pattern={is_scrape} (dup_count={dup_count})")
    print()

    print("--- A key that hits its daily budget ---")
    small_budget = DailyBudgetTracker(daily_budget=3)
    for i in range(5):
        allowed, reason = small_budget.record_and_check("key-heavy-user")
        print(f"  query {i + 1}: allowed={allowed}, reason: {reason}")
    print()

    print("--- Query shape limits ---")
    allowed, reason = validate_query_shape("What is RAG? " * 100)
    print(f"Oversized query: allowed={allowed}, reason: {reason}")
    allowed, reason = validate_query_shape("What is RAG?", batch_size=50)
    print(f"Oversized batch: allowed={allowed}, reason: {reason}")

    print(
        "\nWhy cost attacks matter, and why budgets matter: a per-minute "
        "rate limit alone cannot catch a key sending one request every "
        "few seconds around the clock, far below any reasonable per-"
        "minute threshold, but still thousands of real queries over a "
        "day. A daily budget catches exactly that sustained pattern, "
        "while a scrape detector catches the opposite shape: a tight "
        "burst of near-identical requests trying to extract the whole "
        "index through repeated, narrow queries rather than genuinely "
        "varied use. Neither limit alone covers both attack shapes, "
        "which is why they are layered together, on top of Day 23's "
        "per-minute rate limit, not in place of it."
    )


if __name__ == "__main__":
    main()
