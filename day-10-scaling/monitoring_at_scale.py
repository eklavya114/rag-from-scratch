"""
monitoring_at_scale.py

Shows why averages lie, how to compute real latency percentiles, a
simple alerting rule, and a text-based "dashboard" view -- the kind of
visibility a RAG system needs once it's handling real traffic, not just
your own test queries.
"""

import random
import statistics


def simulate_realistic_latencies(num_requests, seed=42):
    """
    Real latency distributions aren't a tight bell curve around the
    average -- most requests are fast, but a meaningful tail is much
    slower (a slow shard, a cache miss, an unlucky GC pause, a cold
    start). We simulate that explicitly: most requests fast, a small
    fraction much slower, instead of generating uniform or normally
    distributed fake data that would hide exactly the problem percentile
    tracking exists to catch.
    """
    rng = random.Random(seed)
    latencies = []
    for _ in range(num_requests):
        if rng.random() < 0.95:
            latencies.append(rng.gauss(50, 10))   # the normal case: ~50ms
        else:
            latencies.append(rng.gauss(800, 200))  # the slow tail: ~800ms
    return [max(1.0, l) for l in latencies]  # latency can't be negative


def percentile(values, p):
    """
    Computes the p-th percentile the straightforward way: sort, then
    index proportionally. (A production system would use a streaming
    percentile estimator instead of storing every raw value, but the
    definition is the same.)
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, int(len(sorted_values) * p / 100))
    return sorted_values[index]


def why_averages_lie(latencies):
    print("--- Why averages lie ---\n")
    avg = statistics.mean(latencies)
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    worst = max(latencies)

    print(f"Average latency: {avg:.1f} ms")
    print(f"p50 (median):    {p50:.1f} ms")
    print(f"p95:             {p95:.1f} ms")
    print(f"p99:             {p99:.1f} ms")
    print(f"Worst (max):     {worst:.1f} ms\n")
    print(
        f"The average ({avg:.0f}ms) looks fine. But p99 ({p99:.0f}ms) tells a "
        f"very different story: 1 in every 100 requests is dramatically "
        f"slower. If you have thousands of users, that's not a rare edge "
        f"case -- it's a steady stream of bad experiences the average "
        f"completely hides.\n"
    )


def resource_usage_snapshot():
    print("--- Resource usage snapshot ---\n")
    # A fabricated but realistic-shaped snapshot of what you'd actually
    # want visibility into -- the point is WHICH metrics to watch, not
    # live data collection (which needs a real running system).
    metrics = {
        "Memory used": "68% of 16 GB",
        "Index size on disk": "4.2 GB",
        "Active connections": "142",
        "Queries per second (current)": "38 qps",
        "Queries per second (capacity)": "~120 qps",
        "Cache hit rate": "74%",
    }
    for name, value in metrics.items():
        print(f"  {name:<32}: {value}")
    print()


def check_alert_conditions(p99_latency_ms, error_rate_percent, cache_hit_rate_percent):
    """
    ALERT WHEN PERFORMANCE DEGRADES: a few simple, concrete threshold
    rules. Real alerting systems are more sophisticated (trend-based,
    anomaly detection), but the core idea is the same: define what
    "bad" looks like numerically, ahead of time, so degradation gets
    caught automatically instead of relying on someone noticing.
    """
    alerts = []
    if p99_latency_ms > 1200:
        alerts.append(f"HIGH LATENCY: p99 is {p99_latency_ms:.0f}ms (threshold: 1200ms)")
    if error_rate_percent > 1.0:
        alerts.append(f"HIGH ERROR RATE: {error_rate_percent:.1f}% (threshold: 1.0%)")
    if cache_hit_rate_percent < 50.0:
        alerts.append(f"LOW CACHE HIT RATE: {cache_hit_rate_percent:.0f}% (threshold: 50%)")
    return alerts


def print_dashboard(latencies, error_rate, cache_hit_rate):
    print("--- Simple text dashboard ---\n")
    p50, p95, p99 = percentile(latencies, 50), percentile(latencies, 95), percentile(latencies, 99)

    def bar(value, max_value, width=30):
        filled = max(0, min(width, int((value / max_value) * width)))
        return "#" * filled + "-" * (width - filled)

    print(f"  Latency p50  {bar(p50, 1000)} {p50:.0f}ms")
    print(f"  Latency p95  {bar(p95, 1000)} {p95:.0f}ms")
    print(f"  Latency p99  {bar(p99, 1000)} {p99:.0f}ms")
    print(f"  Error rate   {bar(error_rate, 5)} {error_rate:.1f}%")
    print(f"  Cache hits   {bar(cache_hit_rate, 100)} {cache_hit_rate:.0f}%")
    print()


def main():
    print("=== Monitoring at Scale ===\n")

    latencies = simulate_realistic_latencies(1000)
    why_averages_lie(latencies)

    resource_usage_snapshot()

    print_dashboard(latencies, error_rate=0.3, cache_hit_rate=74.0)

    print("--- Alert check ---\n")
    p99 = percentile(latencies, 99)
    alerts = check_alert_conditions(p99_latency_ms=p99, error_rate_percent=0.3, cache_hit_rate_percent=74.0)
    if alerts:
        for alert in alerts:
            print(f"  [ALERT] {alert}")
    else:
        print("  No alerts triggered -- all metrics within normal thresholds.")

    print("\n--- A degraded scenario ---\n")
    degraded_latencies = simulate_realistic_latencies(1000, seed=7)
    degraded_latencies = [l * 3 for l in degraded_latencies]  # simulate a real slowdown
    degraded_p99 = percentile(degraded_latencies, 99)
    alerts = check_alert_conditions(p99_latency_ms=degraded_p99, error_rate_percent=2.1, cache_hit_rate_percent=35.0)
    print(f"  p99 latency: {degraded_p99:.0f}ms, error rate: 2.1%, cache hit rate: 35%")
    for alert in alerts:
        print(f"  [ALERT] {alert}")

    print(
        "\nWhat to actually watch: latency PERCENTILES (not averages), "
        "error rate, cache hit rate, and resource headroom (memory, QPS "
        "capacity). The goal is catching degradation from a dashboard or "
        "an alert -- before a user has to tell you something's wrong."
    )


if __name__ == "__main__":
    main()
