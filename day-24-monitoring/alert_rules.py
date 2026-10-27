"""
alert_rules.py

Alerts defined in plain Python, evaluated against a set of readings. A
real monitoring system (Prometheus's Alertmanager, for example) defines
these in a config file and evaluates them continuously, but the logic is
the same: a condition, checked against recent numbers, that fires or
does not. Keeping the condition itself in a plain function, here, makes
it easy to test with made-up readings before trusting it against real
traffic, exactly what traffic_simulation.py does next.
"""

from dataclasses import dataclass

ERROR_RATE_THRESHOLD = 0.05
P95_LATENCY_THRESHOLD_MS = 200.0
CACHE_HIT_RATE_THRESHOLD = 0.30
IN_FLIGHT_SUSTAINED_THRESHOLD = 20


@dataclass
class Alert:
    name: str
    severity: str  # "warning" or "critical"
    message: str


@dataclass
class Reading:
    """One window's worth of readings: whatever a real metrics snapshot would report over some recent interval."""
    error_rate: float
    p95_latency_ms: float
    cache_hit_rate: float
    in_flight_requests: int


def check_error_rate(reading):
    """
    ALERT: error rate above 5% over the recent window. Error rate is a
    symptom users directly feel (their request failed), which is why it
    gets a LOW threshold and a critical severity: a service failing one
    request in twenty is already a bad experience for real users, not
    just a statistical curiosity.
    """
    if reading.error_rate > ERROR_RATE_THRESHOLD:
        return Alert(
            name="HighErrorRate",
            severity="critical",
            message=f"Error rate is {reading.error_rate:.0%}, above the {ERROR_RATE_THRESHOLD:.0%} threshold.",
        )
    return None


def check_p95_latency(reading):
    """ALERT: p95 latency above the threshold. p95, not the average, since the average can look fine while one in twenty users is actually waiting far longer than that."""
    if reading.p95_latency_ms > P95_LATENCY_THRESHOLD_MS:
        return Alert(
            name="HighP95Latency",
            severity="warning",
            message=f"p95 latency is {reading.p95_latency_ms:.1f} ms, above the {P95_LATENCY_THRESHOLD_MS:.1f} ms threshold.",
        )
    return None


def check_cache_hit_rate(reading):
    """
    ALERT: cache hit rate dropped below the threshold. Not a user-facing
    symptom by itself (a cache miss still serves a correct answer), but
    a leading indicator: a falling hit rate often means more real work
    is about to hit retrieval and generation, which tends to show up as
    rising latency soon after, so this is a WARNING, not critical.
    """
    if reading.cache_hit_rate < CACHE_HIT_RATE_THRESHOLD:
        return Alert(
            name="LowCacheHitRate",
            severity="warning",
            message=f"Cache hit rate is {reading.cache_hit_rate:.0%}, below the {CACHE_HIT_RATE_THRESHOLD:.0%} threshold.",
        )
    return None


def check_in_flight_sustained(readings):
    """
    ALERT: the in-flight gauge stays high across MULTIPLE consecutive
    readings, not just one. A single high reading can be a brief, normal
    burst. The same high value held across several readings in a row
    means requests are piling up faster than the service can finish
    them, a real saturation problem, which is why this check looks at a
    short history instead of one snapshot.
    """
    if len(readings) < 3:
        return None
    if all(r.in_flight_requests >= IN_FLIGHT_SUSTAINED_THRESHOLD for r in readings[-3:]):
        return Alert(
            name="SustainedHighInFlight",
            severity="critical",
            message=f"In-flight requests have stayed at or above {IN_FLIGHT_SUSTAINED_THRESHOLD} for 3 consecutive readings.",
        )
    return None


def evaluate_rules(readings):
    """Evaluates every alert rule against a list of readings (most recent last) and returns the alerts that fire right now."""
    if not readings:
        return []

    latest = readings[-1]
    fired = []

    for check in (check_error_rate, check_p95_latency, check_cache_hit_rate):
        alert = check(latest)
        if alert:
            fired.append(alert)

    sustained_alert = check_in_flight_sustained(readings)
    if sustained_alert:
        fired.append(sustained_alert)

    return fired


def main():
    print("=== Alert Rules ===\n")

    print("--- A healthy reading ---")
    healthy = [Reading(error_rate=0.01, p95_latency_ms=45.0, cache_hit_rate=0.60, in_flight_requests=3)]
    alerts = evaluate_rules(healthy)
    print(f"Alerts fired: {len(alerts)}\n")

    print("--- A reading with multiple problems ---")
    unhealthy = [Reading(error_rate=0.12, p95_latency_ms=350.0, cache_hit_rate=0.10, in_flight_requests=5)]
    alerts = evaluate_rules(unhealthy)
    for alert in alerts:
        print(f"  [{alert.severity.upper()}] {alert.name}: {alert.message}")
    print()

    print("--- Sustained high in-flight requests (3 readings in a row) ---")
    sustained = [
        Reading(error_rate=0.01, p95_latency_ms=50.0, cache_hit_rate=0.50, in_flight_requests=25),
        Reading(error_rate=0.01, p95_latency_ms=55.0, cache_hit_rate=0.50, in_flight_requests=28),
        Reading(error_rate=0.01, p95_latency_ms=60.0, cache_hit_rate=0.50, in_flight_requests=22),
    ]
    alerts = evaluate_rules(sustained)
    for alert in alerts:
        print(f"  [{alert.severity.upper()}] {alert.name}: {alert.message}")
    print()

    print("--- A single high in-flight spike (should NOT fire, only one reading) ---")
    single_spike = [
        Reading(error_rate=0.01, p95_latency_ms=50.0, cache_hit_rate=0.50, in_flight_requests=3),
        Reading(error_rate=0.01, p95_latency_ms=50.0, cache_hit_rate=0.50, in_flight_requests=3),
        Reading(error_rate=0.01, p95_latency_ms=50.0, cache_hit_rate=0.50, in_flight_requests=30),
    ]
    alerts = evaluate_rules(single_spike)
    print(f"Alerts fired: {len(alerts)} (expected 0, the spike is only in the latest reading, not sustained)\n")

    print(
        "Why thresholds need tuning, and alert fatigue: a threshold set "
        "too low fires constantly on normal variation, and people on call "
        "quickly learn to ignore it, so a REAL problem later gets missed "
        "in the noise. A threshold set too high stays silent while real "
        "users are already affected. The in-flight check above requiring "
        "3 CONSECUTIVE readings, not one, is itself an anti-fatigue "
        "choice: brief, normal traffic bursts should never page anyone, "
        "only a sustained problem should."
    )


if __name__ == "__main__":
    main()
