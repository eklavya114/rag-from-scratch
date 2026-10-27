"""
percentile_tracking.py

Shows concretely why percentiles matter more than an average: a mean
blends every value together into one number, which means a handful of
very slow requests can get completely absorbed by a much larger number
of fast ones. Percentiles instead ask "what value did X% of requests
fall at or below," which is exactly the question a real user's
experience depends on: a user does not experience the average, they
experience THEIR OWN request, and p95 or p99 describe what a request
near the slow end of the distribution actually felt like.
"""


def nearest_rank_percentile(values, percentile):
    """
    Computes a percentile using the nearest-rank method: sort the
    values, then pick the one at position ceil(percentile/100 * n),
    1-indexed. Simple, exact (no interpolation), and good enough for
    monitoring purposes, where an approximate percentile from a real
    histogram's buckets is already the norm.
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    rank = max(1, min(n, -(-n * percentile // 100)))  # ceiling division without importing math
    return sorted_values[rank - 1]


def mean(values):
    return sum(values) / len(values) if values else 0.0


def main():
    print("=== Percentile Tracking ===\n")

    # 97 fast, normal requests, plus 3 genuinely slow outliers, mixed in.
    # A realistic shape: most requests are fast, a small handful are not.
    normal_latencies = [20 + (i % 15) for i in range(97)]
    slow_outliers = [850, 920, 1100]
    latencies = normal_latencies + slow_outliers

    print(f"Total requests: {len(latencies)}")
    print(f"Slow outliers among them: {slow_outliers}\n")

    avg = mean(latencies)
    p50 = nearest_rank_percentile(latencies, 50)
    p95 = nearest_rank_percentile(latencies, 95)
    p99 = nearest_rank_percentile(latencies, 99)

    print(f"mean: {avg:.2f} ms")
    print(f"p50:  {p50:.2f} ms")
    print(f"p95:  {p95:.2f} ms")
    print(f"p99:  {p99:.2f} ms\n")

    print(
        f"The mean ({avg:.1f} ms) looks almost identical to a typical "
        f"fast request: it barely moved, because 97 fast requests "
        f"vastly outnumber 3 slow ones in the sum. p99 ({p99:.1f} ms), "
        f"on the other hand, lands right in the slow outliers themselves, "
        f"because that is literally what p99 means: the value at or "
        f"below which 99% of requests fall, so the worst 1% IS what p99 "
        f"is built to surface.\n"
    )

    print("--- What happens if a few more requests become slow ---\n")
    worse_latencies = normal_latencies + [850, 920, 1100, 980, 1050, 870, 930, 990]
    worse_avg = mean(worse_latencies)
    worse_p95 = nearest_rank_percentile(worse_latencies, 95)
    worse_p99 = nearest_rank_percentile(worse_latencies, 99)

    print(f"mean: {worse_avg:.2f} ms (was {avg:.2f} ms)")
    print(f"p95:  {worse_p95:.2f} ms (was {p95:.2f} ms)")
    print(f"p99:  {worse_p99:.2f} ms (was {p99:.2f} ms)")

    print(
        f"\nThe mean did rise here, roughly doubling to {worse_avg:.1f} ms, "
        f"but it still sits well within what looks like ordinary, mildly "
        f"slow traffic, nowhere near the roughly 900 to 1100 ms a real "
        f"user in the slow tail is actually experiencing. p95 tells a "
        f"completely different story: it jumped from {p95:.1f} ms "
        f"straight into the outlier range, because enough of the "
        f"distribution is now slow that the 95th percentile itself "
        f"crosses into the slow tail. This is exactly why "
        f"alert_rules.py's HighP95Latency check watches p95, not the "
        f"mean: the mean's roughly 80% increase still reads as a minor "
        f"blip, while p95 reveals that a meaningful share of real users "
        f"are now hitting genuinely slow requests, not just a few "
        f"unlucky ones."
    )

    print(
        "\nChoosing which percentiles to alert on: p50 describes a "
        "typical request, useful to know but rarely worth paging anyone "
        "over by itself. p95 is the standard choice for alerting, since "
        "it reacts to a real, sizeable slow tail without being thrown off "
        "by one single extreme outlier the way p99 or p99.9 can be. p99 "
        "is still worth TRACKING, since it reveals rare, severe cases "
        "worth investigating, just less often worth an automatic alert on "
        "its own."
    )


if __name__ == "__main__":
    main()
