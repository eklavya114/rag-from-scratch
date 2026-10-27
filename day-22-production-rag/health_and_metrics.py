"""
health_and_metrics.py

Tracks service-level numbers across many requests: how many came in, how
many failed, how often the cache helped, and how long each stage
typically takes. A single request's timing tells you about that one
request. These aggregate numbers tell you whether the service as a whole
is healthy, which is a different and more useful question when deciding
whether to page someone.
"""

ERROR_RATE_DEGRADED_THRESHOLD = 0.05   # above 5% errors: degraded
ERROR_RATE_UNHEALTHY_THRESHOLD = 0.20  # above 20% errors: unhealthy


class ServiceMetrics:
    """Accumulates counts and timings across every request a service handles, so health() can answer from real numbers instead of a guess."""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.stage_timings = {}  # stage name -> list of durations in ms

    def record(self, response):
        """Folds one RagResponse into the running totals. Called once per request, right after RagService.query() returns."""
        self.request_count += 1
        if response.status == "error":
            self.error_count += 1
        if response.cache_hit:
            self.cache_hits += 1
        for stage, duration_ms in response.timings_ms.items():
            if stage == "over_budget":
                continue
            self.stage_timings.setdefault(stage, []).append(duration_ms)

    def error_rate(self):
        return self.error_count / self.request_count if self.request_count else 0.0

    def cache_hit_rate(self):
        return self.cache_hits / self.request_count if self.request_count else 0.0

    def average_latency_per_stage(self):
        return {
            stage: sum(durations) / len(durations)
            for stage, durations in self.stage_timings.items()
        }

    def health(self):
        """
        Reports one of three states:
          "healthy":   error rate below the degraded threshold
          "degraded":  error rate above the degraded threshold, but below unhealthy
          "unhealthy": error rate above the unhealthy threshold
        Alert on "unhealthy" immediately. Alert on "degraded" if it
        persists across more than a handful of requests, since a single
        bad batch of input shouldn't page anyone by itself.
        """
        if self.request_count == 0:
            return "healthy"  # no traffic yet is not the same as a broken service

        rate = self.error_rate()
        if rate >= ERROR_RATE_UNHEALTHY_THRESHOLD:
            return "unhealthy"
        if rate >= ERROR_RATE_DEGRADED_THRESHOLD:
            return "degraded"
        return "healthy"


def main():
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from config import Config
    from rag_service import RagService

    print("=== Health and Metrics ===\n")

    service = RagService(Config())
    metrics = ServiceMetrics()

    queries = [
        "What is RAG?",
        "What is a vector database?",
        "What is RAG?",  # repeat, cache hit
        "What programming language is easy to read?",
        "",  # rejected, not an error
        "What is RAG?",  # repeat, cache hit
    ]

    for query_text in queries:
        response = service.query(query_text)
        metrics.record(response)

    print(f"Request count:    {metrics.request_count}")
    print(f"Error count:      {metrics.error_count}")
    print(f"Error rate:       {metrics.error_rate():.0%}")
    print(f"Cache hit rate:   {metrics.cache_hit_rate():.0%}")
    print(f"Health:           {metrics.health()}")

    print("\nAverage latency per stage (ms):")
    for stage, avg_ms in metrics.average_latency_per_stage().items():
        print(f"  {stage:<14} {avg_ms:.4f}")

    print(
        "\nWhat to alert on: health() moving to 'unhealthy' should page "
        "someone immediately, since one in five requests failing means "
        "something is seriously broken. 'degraded' is worth watching, but "
        "a single rejected request (an empty query, for example) is not an "
        "error and should never count toward error_rate, exactly why "
        "rejected and no_results are tracked separately from error above."
    )


if __name__ == "__main__":
    main()
