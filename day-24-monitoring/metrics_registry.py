"""
metrics_registry.py

A tiny metrics library, standard library only, modeled on the three
metric types nearly every real monitoring system builds around:

  Counter:   only ever goes up (total requests, total errors). Use it
             for anything you are counting occurrences of.
  Gauge:     goes up AND down (in-flight requests, queue depth). Use it
             for anything that has a current value, not just a total.
  Histogram: buckets observed values into ranges (request latency). Use
             it when you need percentiles later, not just an average,
             since an average alone hides the slow tail.

Every metric supports LABELS (for example route="/query",
status="ok"), since "how many requests" is rarely as useful a question
as "how many requests, for THIS route, with THIS status." Labels turn
one metric into a small table of related counts instead of one number.

All updates go through a lock, since a real service handles requests
concurrently (Day 23's ThreadingHTTPServer, for example), and metrics
updated from multiple threads at once without a lock can silently lose
increments.
"""

import threading


def _label_key(labels):
    """Turns a labels dict into a stable, hashable key, sorted so the same labels always produce the same key regardless of insertion order."""
    return tuple(sorted((labels or {}).items()))


def _format_labels(labels):
    """Formats labels in Prometheus text format: {key="value",key2="value2"}, or nothing at all if there are no labels."""
    if not labels:
        return ""
    pairs = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"{{{pairs}}}"


class Counter:
    """A monotonically increasing count, per distinct set of labels."""

    def __init__(self, name, help_text):
        self.name = name
        self.help_text = help_text
        self._values = {}  # label_key -> count
        self._lock = threading.Lock()

    def inc(self, labels=None, amount=1):
        key = _label_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + amount

    def value(self, labels=None):
        with self._lock:
            return self._values.get(_label_key(labels), 0)

    def render(self):
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} counter"]
        with self._lock:
            items = list(self._values.items())
        for key, count in items:
            labels = dict(key)
            lines.append(f"{self.name}{_format_labels(labels)} {count}")
        return lines


class Gauge:
    """A value that can go up or down, representing a current state rather than a running total."""

    def __init__(self, name, help_text):
        self.name = name
        self.help_text = help_text
        self._values = {}
        self._lock = threading.Lock()

    def set(self, value, labels=None):
        key = _label_key(labels)
        with self._lock:
            self._values[key] = value

    def inc(self, labels=None, amount=1):
        key = _label_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + amount

    def dec(self, labels=None, amount=1):
        self.inc(labels, -amount)

    def value(self, labels=None):
        with self._lock:
            return self._values.get(_label_key(labels), 0)

    def render(self):
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} gauge"]
        with self._lock:
            items = list(self._values.items())
        for key, val in items:
            labels = dict(key)
            lines.append(f"{self.name}{_format_labels(labels)} {val}")
        return lines


DEFAULT_LATENCY_BUCKETS_MS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, float("inf")]


class Histogram:
    """
    Buckets observed values (typically latencies, in milliseconds) into
    fixed ranges, and also tracks the running sum and count, which is
    how Prometheus-style histograms work: each bucket counts how many
    observations were LESS THAN OR EQUAL TO its upper bound, cumulative,
    so the last bucket (+Inf) always equals the total count.
    """

    def __init__(self, name, help_text, buckets=None):
        self.name = name
        self.help_text = help_text
        self.buckets = buckets or DEFAULT_LATENCY_BUCKETS_MS
        self._bucket_counts = {}  # label_key -> list of cumulative counts, one per bucket
        self._sums = {}
        self._counts = {}
        self._raw_observations = {}  # label_key -> list of raw values, kept for exact percentile computation
        self._lock = threading.Lock()

    def observe(self, value, labels=None):
        key = _label_key(labels)
        with self._lock:
            bucket_counts = self._bucket_counts.setdefault(key, [0] * len(self.buckets))
            for i, upper_bound in enumerate(self.buckets):
                if value <= upper_bound:
                    bucket_counts[i] += 1
            self._sums[key] = self._sums.get(key, 0.0) + value
            self._counts[key] = self._counts.get(key, 0) + 1
            self._raw_observations.setdefault(key, []).append(value)

    def observations(self, labels=None):
        """Returns the raw list of observed values for one label set, used by percentile_tracking.py to compute exact percentiles rather than bucket estimates."""
        with self._lock:
            return list(self._raw_observations.get(_label_key(labels), []))

    def render(self):
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
        with self._lock:
            label_keys = list(self._bucket_counts.keys())
            bucket_counts = dict(self._bucket_counts)
            sums = dict(self._sums)
            counts = dict(self._counts)
        for key in label_keys:
            labels = dict(key)
            for i, upper_bound in enumerate(self.buckets):
                bucket_label = dict(labels)
                bucket_label["le"] = "+Inf" if upper_bound == float("inf") else str(upper_bound)
                lines.append(f"{self.name}_bucket{_format_labels(bucket_label)} {bucket_counts[key][i]}")
            lines.append(f"{self.name}_sum{_format_labels(labels)} {sums[key]}")
            lines.append(f"{self.name}_count{_format_labels(labels)} {counts[key]}")
        return lines


class MetricsRegistry:
    """Holds every metric a service defines, and renders all of them together in Prometheus text format with one call."""

    def __init__(self):
        self._metrics = []

    def register(self, metric):
        self._metrics.append(metric)
        return metric

    def render_prometheus(self):
        """Returns the full Prometheus text exposition format: every registered metric's HELP, TYPE, and value lines, in order."""
        lines = []
        for metric in self._metrics:
            lines.extend(metric.render())
        return "\n".join(lines) + "\n"


def main():
    print("=== Metrics Registry ===\n")

    registry = MetricsRegistry()

    requests_total = registry.register(Counter("requests_total", "Total requests handled, by status."))
    cache_hits_total = registry.register(Counter("cache_hits_total", "Total cache hits."))
    request_latency_ms = registry.register(Histogram("request_latency_ms", "Request latency in milliseconds."))

    requests_total.inc({"status": "ok"})
    requests_total.inc({"status": "ok"})
    requests_total.inc({"status": "ok"})
    requests_total.inc({"status": "rejected"})
    requests_total.inc({"status": "error"})

    cache_hits_total.inc()
    cache_hits_total.inc()

    for latency in [2.1, 8.5, 15.0, 42.3, 120.7, 310.2]:
        request_latency_ms.observe(latency)

    print("--- Counter values ---")
    print(f"requests_total(status=ok): {requests_total.value({'status': 'ok'})}")
    print(f"requests_total(status=rejected): {requests_total.value({'status': 'rejected'})}")
    print(f"requests_total(status=error): {requests_total.value({'status': 'error'})}")
    print(f"cache_hits_total: {cache_hits_total.value()}")

    print("\n--- Rendered Prometheus text format ---\n")
    print(registry.render_prometheus())

    print(
        "Why each metric type: a Counter answers 'how many, ever' and "
        "only moves one direction, which is what makes a sudden drop in "
        "its rate (not its value) worth investigating. A Gauge answers "
        "'what is the current state right now', useful for anything that "
        "can recover on its own (in-flight requests dropping back to "
        "zero). A Histogram answers 'what does the DISTRIBUTION of values "
        "look like', which a single average could never show, exactly "
        "why percentile_tracking.py later builds on the raw observations "
        "this histogram keeps."
    )


if __name__ == "__main__":
    main()
