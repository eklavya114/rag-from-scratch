"""
cache_statistics.py

Monitoring for a cache specifically: hit rate, miss rate, size over
time, and memory usage, shown as both a running log and a simple
dashboard -- using the same percentile-over-average discipline Day 10's
monitoring_at_scale.py established, applied here to cache behavior.
"""

import random
import sys


class MonitoredCache:
    """A cache instrumented to record its own history over time, not just a final hit/miss total."""

    def __init__(self, max_size):
        self.max_size = max_size
        self.store = {}
        self.access_order = []  # for simple LRU eviction
        self.hits = 0
        self.misses = 0
        self.history = []  # one entry per operation: {"hit": bool, "size": int}

    def get(self, key):
        if key in self.store:
            self.hits += 1
            self.access_order.remove(key)
            self.access_order.append(key)
            self.history.append({"hit": True, "size": len(self.store)})
            return self.store[key]
        self.misses += 1
        self.history.append({"hit": False, "size": len(self.store)})
        return None

    def set(self, key, value):
        if key not in self.store and len(self.store) >= self.max_size:
            evicted = self.access_order.pop(0)
            del self.store[evicted]
        self.store[key] = value
        if key not in self.access_order:
            self.access_order.append(key)

    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def estimate_memory_bytes(self, avg_value_size_bytes=200):
        """A rough estimate -- real memory accounting would need to measure actual object sizes, same honest approximation Day 10's measure_memory() used."""
        return len(self.store) * avg_value_size_bytes


def track_hit_rate_over_time(cache, requests, window_size=20):
    """
    Computes hit rate in SLIDING WINDOWS, not just one final number --
    the same "an average can hide a real trend" lesson from Day 10's
    monitoring_at_scale.py, applied to cache health over time instead of
    latency.
    """
    windowed_rates = []
    for i in range(0, len(requests), window_size):
        window = cache.history[i:i + window_size]
        if not window:
            continue
        window_hits = sum(1 for entry in window if entry["hit"])
        windowed_rates.append(window_hits / len(window))
    return windowed_rates


def check_cache_alerts(hit_rate, size, max_size, min_acceptable_hit_rate=0.3):
    """ALERT WHEN CACHE HEALTH DEGRADES: concrete, numeric thresholds -- the same discipline as Day 10's check_alert_conditions()."""
    alerts = []
    if hit_rate < min_acceptable_hit_rate:
        alerts.append(f"LOW HIT RATE: {hit_rate:.0%} (threshold: {min_acceptable_hit_rate:.0%}) -- cache may be too small, or traffic has no real repeats")
    if size >= max_size:
        alerts.append(f"CACHE AT CAPACITY: {size}/{max_size} entries -- evictions are happening on every new key")
    return alerts


def print_dashboard(cache, windowed_rates):
    def bar(value, max_value, width=30):
        filled = max(0, min(width, int((value / max_value) * width)))
        return "#" * filled + "-" * (width - filled)

    print("--- Cache Dashboard ---\n")
    print(f"  Overall hit rate   {bar(cache.hit_rate(), 1.0)} {cache.hit_rate():.0%}")
    print(f"  Cache size         {bar(len(cache.store), cache.max_size)} {len(cache.store)}/{cache.max_size}")
    memory_kb = cache.estimate_memory_bytes() / 1024
    print(f"  Est. memory        {bar(memory_kb, 50)} {memory_kb:.1f} KB")
    print()
    print("  Hit rate over time (windowed):")
    for i, rate in enumerate(windowed_rates):
        print(f"    window {i+1}: {bar(rate, 1.0, width=20)} {rate:.0%}")


def main():
    print("=== Cache Statistics and Monitoring ===\n")

    rng = random.Random(42)
    popular_keys = [f"key_{i}" for i in range(5)]
    rare_keys = [f"key_{i}" for i in range(5, 40)]

    # Simulate traffic that starts well-behaved (lots of repeats), then
    # shifts to mostly-unique queries (a realistic "traffic composition
    # changed" scenario) -- so the windowed hit rate actually shows a
    # real trend, not just noise around one stable average.
    requests = []
    for _ in range(60):
        requests.append(rng.choice(popular_keys) if rng.random() < 0.85 else rng.choice(rare_keys))
    for _ in range(60):
        requests.append(rng.choice(popular_keys) if rng.random() < 0.15 else rng.choice(rare_keys))

    cache = MonitoredCache(max_size=10)
    for key in requests:
        if cache.get(key) is None:
            cache.set(key, f"value_for_{key}")

    windowed_rates = track_hit_rate_over_time(cache, requests, window_size=20)
    print_dashboard(cache, windowed_rates)

    print("\n--- Alert check ---\n")
    alerts = check_cache_alerts(cache.hit_rate(), len(cache.store), cache.max_size)
    final_window_rate = windowed_rates[-1] if windowed_rates else cache.hit_rate()
    recent_alerts = check_cache_alerts(final_window_rate, len(cache.store), cache.max_size)

    print(f"Based on OVERALL hit rate ({cache.hit_rate():.0%}):")
    for alert in alerts:
        print(f"  [ALERT] {alert}")
    if not alerts:
        print("  No alerts.")

    print(f"\nBased on MOST RECENT window's hit rate ({final_window_rate:.0%}):")
    for alert in recent_alerts:
        print(f"  [ALERT] {alert}")
    if not recent_alerts:
        print("  No alerts.")

    print(
        "\nWhy windowed tracking matters: the OVERALL hit rate blends the "
        "well-behaved early traffic with the later traffic shift, hiding "
        "exactly when and how much things degraded. Checking the MOST "
        "RECENT window specifically catches a real, current problem (the "
        "traffic composition changed, repeats dried up) that an "
        "all-time-average number would mask for a long time -- the same "
        "percentile-over-average lesson from Day 10, applied here to cache "
        "health instead of latency."
    )


if __name__ == "__main__":
    main()
