"""
distributed_caching.py

A single-process cache (everything we've built so far this folder) only
helps that one process. Once a system runs on multiple servers, each
with its own local cache, two new problems appear: a cache miss on one
server might be a cache HIT on another, and if the underlying data
changes, every server's cache needs to find out -- the cache coherence
problem.
"""

import time


class LocalCache:
    """A cache that lives only in this one process's memory -- fast, but invisible to any other process."""

    def __init__(self, access_latency_ms=0.001):
        self.store = {}
        self.access_latency_ms = access_latency_ms  # simulates real in-memory access time
        self.hits = 0
        self.misses = 0

    def get(self, key):
        time.sleep(self.access_latency_ms / 1000)
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, key, value):
        self.store[key] = value


class RemoteCache:
    """
    Simulates a shared cache service (like Redis or Memcached) that
    EVERY server talks to over the network. Slower per-access than a
    local cache (real network round-trip), but shared -- a value cached
    by one server is immediately visible to every other server.
    """

    def __init__(self, access_latency_ms=2.0):
        self.store = {}  # the single shared store, standing in for the remote service
        self.access_latency_ms = access_latency_ms
        self.hits = 0
        self.misses = 0

    def get(self, key):
        time.sleep(self.access_latency_ms / 1000)
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, key, value):
        time.sleep(self.access_latency_ms / 1000)
        self.store[key] = value


class TwoTierCache:
    """
    LOCAL + REMOTE, checked in order: local first (fast, might miss
    because this server hasn't seen the key before), then remote
    (slower, but shared across every server). A remote hit also
    populates the local cache, so the NEXT request on this same server
    for the same key becomes a fast local hit.
    """

    def __init__(self, local_cache, remote_cache):
        self.local = local_cache
        self.remote = remote_cache

    def get(self, key):
        value = self.local.get(key)
        if value is not None:
            return value, "local_hit"

        value = self.remote.get(key)
        if value is not None:
            self.local.set(key, value)  # promote to local for next time
            return value, "remote_hit"

        return None, "miss"

    def set(self, key, value):
        self.local.set(key, value)
        self.remote.set(key, value)


def simulate_two_servers_sharing_remote_cache():
    """
    Demonstrates the actual benefit of a shared remote cache: Server A
    computes and caches something. Server B, which has NEVER seen this
    key in its own local cache, still gets a (slower, but real) hit via
    the shared remote cache -- instead of recomputing from scratch.
    """
    shared_remote = RemoteCache(access_latency_ms=2.0)

    server_a = TwoTierCache(LocalCache(), shared_remote)
    server_b = TwoTierCache(LocalCache(), shared_remote)

    print("Server A computes and caches 'What is RAG?' for the first time...")
    server_a.set("What is RAG?", "RAG retrieves documents before generating an answer.")

    print("Server B (never seen this key locally) requests the same key:")
    value, path = server_b.get("What is RAG?")
    print(f"  Result: \"{value}\" via {path}\n")

    print("Server B requests it AGAIN (now in its own local cache too):")
    value, path = server_b.get("What is RAG?")
    print(f"  Result: \"{value}\" via {path}")


def measure_latency_tradeoff():
    local = LocalCache(access_latency_ms=0.001)
    remote = RemoteCache(access_latency_ms=2.0)

    local.set("key", "value")
    remote.set("key", "value")

    start = time.perf_counter()
    for _ in range(20):
        local.get("key")
    local_time = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    for _ in range(20):
        remote.get("key")
    remote_time = (time.perf_counter() - start) * 1000

    return local_time, remote_time


def main():
    print("=== Distributed Caching ===\n")

    print("--- Local vs. remote access latency (20 lookups each) ---\n")
    local_time, remote_time = measure_latency_tradeoff()
    print(f"Local cache:  {local_time:.2f} ms total ({local_time/20:.3f} ms/lookup)")
    print(f"Remote cache: {remote_time:.2f} ms total ({remote_time/20:.3f} ms/lookup)")
    print(f"Remote is {remote_time/local_time:.0f}x slower per lookup, but SHARED across every server.\n")

    print("--- Cache coherence: a shared remote cache benefits ALL servers ---\n")
    simulate_two_servers_sharing_remote_cache()

    print(
        "\n--- Latency vs. storage tradeoff ---\n"
        "Local-only caching: fastest possible access, but each server\n"
        "  builds up its own cache independently -- the SAME question asked\n"
        "  on two different servers is a cold miss on each one separately,\n"
        "  wasting the exact redundant work caching exists to avoid.\n"
        "Remote-only caching: every server shares one cache, maximizing\n"
        "  reuse across the whole fleet, at the cost of a network round-\n"
        "  trip on every single access, even for something just looked up\n"
        "  a moment ago.\n"
        "Two-tier (local + remote): the common real-world answer -- most\n"
        "  requests hit fast locally once 'warm' on that server, and a\n"
        "  local miss still has a real chance to hit the shared remote\n"
        "  cache instead of falling all the way back to full recomputation.\n"
        "  The cost is complexity: now there are two caches to keep\n"
        "  reasonably in sync, which is exactly the coherence problem\n"
        "  cache_invalidation.py addresses next."
    )


if __name__ == "__main__":
    main()
