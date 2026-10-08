"""
cache_eviction_strategies.py

A cache can't grow forever -- at some point something has to be evicted
to make room. Four strategies for deciding WHAT to evict, each measured
on the same realistic (skewed, repeating) traffic pattern so their real
behavior is comparable, not just described.
"""

import random
import sys
from collections import OrderedDict


def generate_realistic_traffic(num_requests, num_unique_keys, popularity_skew=0.7, seed=42):
    """Same long-tail traffic shape as Day 10's caching_strategies.py: a small set of popular keys, a larger set of rare ones."""
    rng = random.Random(seed)
    num_popular = max(1, int(num_unique_keys * 0.2))
    popular_keys = [f"key_{i}" for i in range(num_popular)]
    rare_keys = [f"key_{i}" for i in range(num_popular, num_unique_keys)]

    requests = []
    for _ in range(num_requests):
        if rng.random() < popularity_skew:
            requests.append(rng.choice(popular_keys))
        else:
            requests.append(rng.choice(rare_keys))
    return requests


class LRUCache:
    """LEAST RECENTLY USED: evicts whichever entry hasn't been accessed in the longest time. Assumes recent access predicts near-future access."""

    def __init__(self, max_size):
        self.max_size = max_size
        self.store = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key):
        if key in self.store:
            self.store.move_to_end(key)  # mark as most-recently-used
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, key, value):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.max_size:
            self.store.popitem(last=False)  # evict least-recently-used
            self.evictions += 1


class LFUCache:
    """LEAST FREQUENTLY USED: evicts whichever entry has been accessed the fewest total times. Assumes overall popularity predicts future access better than recency does."""

    def __init__(self, max_size):
        self.max_size = max_size
        self.store = {}
        self.frequency = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key):
        if key in self.store:
            self.frequency[key] += 1
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, key, value):
        if key not in self.store and len(self.store) >= self.max_size:
            least_frequent_key = min(self.frequency, key=self.frequency.get)
            del self.store[least_frequent_key]
            del self.frequency[least_frequent_key]
            self.evictions += 1
        self.store[key] = value
        self.frequency[key] = self.frequency.get(key, 0) + 1


class TTLCache:
    """TIME TO LIVE: every entry expires after a fixed number of "ticks" regardless of how often it's used. Simulates time explicitly via a counter, since this is about staleness, not raw LRU/LFU performance."""

    def __init__(self, max_size, ttl_ticks):
        self.max_size = max_size
        self.ttl_ticks = ttl_ticks
        self.store = {}  # key -> (value, expires_at_tick)
        self.current_tick = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0

    def tick(self):
        self.current_tick += 1

    def get(self, key):
        if key in self.store:
            value, expires_at = self.store[key]
            if self.current_tick >= expires_at:
                del self.store[key]
                self.expirations += 1
                self.misses += 1
                return None
            self.hits += 1
            return value
        self.misses += 1
        return None

    def set(self, key, value):
        if key not in self.store and len(self.store) >= self.max_size:
            oldest_key = min(self.store, key=lambda k: self.store[k][1])
            del self.store[oldest_key]
            self.evictions += 1
        self.store[key] = (value, self.current_tick + self.ttl_ticks)


class HybridCache:
    """
    HYBRID (LRU + frequency floor): evicts the least-recently-used entry,
    same as LRU, EXCEPT it protects entries above a frequency threshold
    from eviction even if they haven't been used recently -- combining
    LRU's recency-awareness with LFU's protection for consistently
    popular items that might otherwise get evicted during a temporary
    lull.
    """

    def __init__(self, max_size, protect_above_frequency=5):
        self.max_size = max_size
        self.protect_above_frequency = protect_above_frequency
        self.store = OrderedDict()
        self.frequency = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            self.frequency[key] = self.frequency.get(key, 0) + 1
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, key, value):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        self.frequency.setdefault(key, 0)

        while len(self.store) > self.max_size:
            evictable_key = None
            for candidate_key in self.store:
                if self.frequency.get(candidate_key, 0) < self.protect_above_frequency:
                    evictable_key = candidate_key
                    break
            if evictable_key is None:
                # Every remaining entry is "protected" -- have to evict
                # the actual least-recently-used one anyway, since the
                # cache can't exceed max_size no matter what.
                evictable_key = next(iter(self.store))
            del self.store[evictable_key]
            self.frequency.pop(evictable_key, None)
            self.evictions += 1


def run_strategy(cache, requests, cost_fn):
    for key in requests:
        if cache.get(key) is None:
            cache.set(key, cost_fn(key))


def main():
    print("=== Cache Eviction Strategies ===\n")

    requests = generate_realistic_traffic(num_requests=500, num_unique_keys=50, popularity_skew=0.75)
    max_size = 10  # deliberately small so eviction actually has to happen

    cost_fn = lambda key: f"value_for_{key}"

    strategies = {
        "LRU": LRUCache(max_size),
        "LFU": LFUCache(max_size),
        "Hybrid": HybridCache(max_size, protect_above_frequency=8),
    }

    for name, cache in strategies.items():
        run_strategy(cache, requests, cost_fn)
        hit_rate = cache.hits / (cache.hits + cache.misses)
        print(f"{name:<8}: hit rate {hit_rate:.1%}, {cache.evictions} evictions, final size {len(cache.store)}")

    print("\n--- TTL separately (needs explicit time simulation) ---\n")
    ttl_cache = TTLCache(max_size, ttl_ticks=20)
    for key in requests:
        if ttl_cache.get(key) is None:
            ttl_cache.set(key, cost_fn(key))
        ttl_cache.tick()
    ttl_hit_rate = ttl_cache.hits / (ttl_cache.hits + ttl_cache.misses)
    print(f"TTL (ttl=20 ticks): hit rate {ttl_hit_rate:.1%}, {ttl_cache.evictions} size-evictions, "
          f"{ttl_cache.expirations} time-expirations, final size {len(ttl_cache.store)}")

    print(
        "\n--- Tradeoffs ---\n"
        "LRU: simple, works well when 'recently used' predicts 'will be\n"
        "  used again soon' -- vulnerable to a burst of one-off queries\n"
        "  evicting genuinely popular entries that just weren't asked in\n"
        "  the last few requests.\n"
        "LFU: protects consistently popular entries better, but can get\n"
        "  stuck keeping an old favorite that was popular once but is no\n"
        "  longer relevant, since frequency never decays on its own here.\n"
        "TTL: the only strategy that handles STALENESS, not just memory --\n"
        "  necessary when underlying data can change, regardless of how\n"
        "  often an entry is accessed.\n"
        "Hybrid: tries to get LRU's adaptability with LFU's protection for\n"
        "  genuinely hot entries, at the cost of being the most complex to\n"
        "  reason about and tune (the frequency threshold is its own\n"
        "  parameter to get right)."
    )


if __name__ == "__main__":
    main()
