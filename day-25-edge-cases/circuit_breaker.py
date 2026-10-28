"""
circuit_breaker.py

A circuit breaker stops calling a dependency that keeps failing,
instead of letting every caller keep waiting on (and retrying) a call
that is very likely to fail again. Three states, the standard shape:

  CLOSED:    normal operation, calls go through, failures are counted.
  OPEN:      too many consecutive failures happened, so calls fail FAST
             without even attempting the real call, for a cooldown period.
  HALF_OPEN: after the cooldown, exactly one probe call is allowed
             through. If it succeeds, the circuit closes again. If it
             fails, the circuit reopens for another cooldown.
"""

import time

FAILURE_THRESHOLD = 3
COOLDOWN_SECONDS = 0.3  # short, for a fast demo; a real system would use minutes


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open, so callers can tell this apart from the dependency's own real failures."""


class CircuitBreaker:
    def __init__(self, failure_threshold=FAILURE_THRESHOLD, cooldown_seconds=COOLDOWN_SECONDS):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = "closed"
        self.consecutive_failures = 0
        self.opened_at = None

    def _maybe_recover(self):
        """Moves OPEN to HALF_OPEN once the cooldown has elapsed, checked lazily on each call rather than with a background timer, simple and sufficient for this project's scale."""
        if self.state == "open" and time.perf_counter() - self.opened_at >= self.cooldown_seconds:
            self.state = "half_open"

    def call(self, fn, *args, **kwargs):
        """
        Runs fn through the breaker. Raises CircuitOpenError immediately
        if the circuit is open (failing FAST, without even attempting
        the real call). In the half-open state, exactly one call is
        allowed through as a probe: success closes the circuit, failure
        reopens it.
        """
        self._maybe_recover()

        if self.state == "open":
            raise CircuitOpenError("Circuit is open: failing fast without attempting the call.")

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _record_failure(self):
        self.consecutive_failures += 1
        if self.state == "half_open":
            # The probe call failed: reopen immediately, for a fresh cooldown.
            self.state = "open"
            self.opened_at = time.perf_counter()
        elif self.consecutive_failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.perf_counter()

    def _record_success(self):
        self.consecutive_failures = 0
        if self.state == "half_open":
            self.state = "closed"


def flaky_dependency(call_log, should_fail_calls):
    """
    A fake dependency that fails on specific call numbers (1-indexed),
    everything else succeeds. Standing in for a real dependency that is
    reliably broken for a known stretch of time. Counts only ACTUAL
    attempts that reach this function, which will be fewer than the
    number of times breaker.call() was invoked whenever the circuit
    failed fast and skipped calling this function at all.
    """
    call_log.append(1)
    real_call_number = len(call_log)
    if real_call_number in should_fail_calls:
        raise RuntimeError(f"Simulated failure on real attempt {real_call_number}.")
    return f"success on real attempt {real_call_number}"


def main():
    print("=== Circuit Breaker ===\n")

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.2)
    call_log = []
    # Calls 1, 2, 3 fail (opens the circuit after 3 consecutive failures).
    # Call 7 onward succeed (the probe, once the cooldown passes, should succeed).
    should_fail_calls = {1, 2, 3}

    for attempt_number in range(1, 8):
        try:
            result = breaker.call(flaky_dependency, call_log, should_fail_calls)
            print(f"Attempt {attempt_number}: SUCCESS -> {result}  (state: {breaker.state})")
        except CircuitOpenError:
            print(f"Attempt {attempt_number}: FAILED FAST, circuit open, dependency never called  (state: {breaker.state})")
        except RuntimeError as e:
            print(f"Attempt {attempt_number}: REAL FAILURE -> {e}  (state: {breaker.state})")

        if attempt_number == 4:
            print(f"  (waiting {breaker.cooldown_seconds}s for the cooldown to elapse...)")
            time.sleep(breaker.cooldown_seconds + 0.05)

    print(
        "\nWhy failing fast protects both sides: without a circuit "
        "breaker, every caller hitting a dependency that is reliably "
        "down would still wait out a full timeout on every single "
        "attempt, wasting their own time for a result they could have "
        "predicted. The DEPENDENCY benefits too: a struggling service "
        "already under load gets no relief if every caller keeps "
        "retrying it at full volume, while an open circuit gives it a "
        "real cooldown window with reduced traffic, a chance to actually "
        "recover instead of being kept at the same load that broke it in "
        "the first place."
    )


if __name__ == "__main__":
    main()
