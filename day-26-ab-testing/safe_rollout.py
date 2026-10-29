"""
safe_rollout.py

Rolls out a winning variant in stages (1%, 10%, 50%, 100%) instead of
switching every user over at once. At each stage, GUARDRAIL metrics are
checked against the baseline before advancing. A guardrail is different
from the main goal metric: the goal metric (helpfulness, here) is what
you are trying to IMPROVE, a guardrail (error rate, p95 latency) is
something that must NOT get worse, even while chasing an improvement
elsewhere. A rollout that improves helpfulness while quietly breaking
latency for everyone is not actually a safe win.
"""

ROLLOUT_STAGES = [0.01, 0.10, 0.50, 1.00]

GUARDRAIL_THRESHOLDS = {
    "error_rate_max": 0.05,          # must not exceed 5%
    "p95_latency_max_ms": 200.0,     # must not exceed 200ms
    "helpfulness_min_ratio": 0.90,   # must stay at least 90% of baseline helpfulness
}


def check_guardrails(baseline, candidate, thresholds=GUARDRAIL_THRESHOLDS):
    """
    Checks a candidate stage's metrics against the guardrail thresholds,
    using baseline's helpfulness rate as the reference point for the
    helpfulness guardrail specifically (a relative check, not an
    absolute one, since "good enough" helpfulness depends on what the
    service already achieves). Returns (passed, list_of_violations).
    """
    violations = []

    if candidate["error_rate"] > thresholds["error_rate_max"]:
        violations.append(f"error_rate {candidate['error_rate']:.1%} exceeds the {thresholds['error_rate_max']:.0%} maximum.")

    if candidate["p95_latency_ms"] > thresholds["p95_latency_max_ms"]:
        violations.append(f"p95_latency_ms {candidate['p95_latency_ms']:.1f} exceeds the {thresholds['p95_latency_max_ms']:.1f}ms maximum.")

    min_acceptable_helpfulness = baseline["helpfulness_rate"] * thresholds["helpfulness_min_ratio"]
    if candidate["helpfulness_rate"] < min_acceptable_helpfulness:
        violations.append(
            f"helpfulness_rate {candidate['helpfulness_rate']:.1%} is below "
            f"{thresholds['helpfulness_min_ratio']:.0%} of baseline ({min_acceptable_helpfulness:.1%})."
        )

    return len(violations) == 0, violations


def run_rollout(baseline, stage_metrics, stages=ROLLOUT_STAGES):
    """
    Walks through each rollout stage in order. stage_metrics maps each
    stage fraction to the metrics observed AT that stage, standing in
    for what a real monitoring system would report once that percentage
    of traffic is actually live on the new variant. Stops and rolls back
    the moment any stage's guardrails fail, rather than continuing
    forward and hoping the next stage looks better.
    """
    log = []
    for stage in stages:
        metrics = stage_metrics[stage]
        passed, violations = check_guardrails(baseline, metrics)

        if passed:
            log.append({"stage": stage, "result": "advanced", "metrics": metrics, "violations": []})
        else:
            log.append({"stage": stage, "result": "rolled_back", "metrics": metrics, "violations": violations})
            break  # stop the rollout immediately, do not attempt later stages

    return log


def print_rollout_log(name, log):
    print(f"--- {name} ---")
    for entry in log:
        print(f"  Stage {entry['stage']:.0%}: {entry['result']}")
        print(f"    error_rate={entry['metrics']['error_rate']:.1%}, "
              f"p95_latency_ms={entry['metrics']['p95_latency_ms']:.1f}, "
              f"helpfulness_rate={entry['metrics']['helpfulness_rate']:.1%}")
        for violation in entry["violations"]:
            print(f"    VIOLATION: {violation}")
    print()


def main():
    print("=== Safe Rollout ===\n")

    baseline = {"error_rate": 0.02, "p95_latency_ms": 90.0, "helpfulness_rate": 0.80}

    print("--- Scenario 1: a clean rollout, every stage passes ---\n")
    clean_stage_metrics = {
        0.01: {"error_rate": 0.02, "p95_latency_ms": 85.0, "helpfulness_rate": 0.82},
        0.10: {"error_rate": 0.02, "p95_latency_ms": 88.0, "helpfulness_rate": 0.83},
        0.50: {"error_rate": 0.03, "p95_latency_ms": 92.0, "helpfulness_rate": 0.84},
        1.00: {"error_rate": 0.02, "p95_latency_ms": 90.0, "helpfulness_rate": 0.85},
    }
    clean_log = run_rollout(baseline, clean_stage_metrics)
    print_rollout_log("Clean rollout log", clean_log)

    print("--- Scenario 2: latency rises at 10%, rollout stops and rolls back ---\n")
    broken_stage_metrics = {
        0.01: {"error_rate": 0.02, "p95_latency_ms": 88.0, "helpfulness_rate": 0.81},
        0.10: {"error_rate": 0.03, "p95_latency_ms": 310.0, "helpfulness_rate": 0.82},
        0.50: {"error_rate": 0.02, "p95_latency_ms": 90.0, "helpfulness_rate": 0.85},  # never reached
        1.00: {"error_rate": 0.02, "p95_latency_ms": 90.0, "helpfulness_rate": 0.85},  # never reached
    }
    broken_log = run_rollout(baseline, broken_stage_metrics)
    print_rollout_log("Rollback rollout log", broken_log)

    print(
        "Why guardrails are different from the main goal metric: "
        "helpfulness is what this rollout is TRYING to improve, and both "
        "scenarios above actually improve it at every stage they reach. "
        "But scenario 2's latency guardrail still correctly stops the "
        "rollout, because a 220 millisecond latency spike is a real "
        "regression for every single user at that stage, regardless of "
        "whether helpfulness also went up. A rollout process that only "
        "watches the goal metric would have sailed right past that "
        "latency spike and rolled it out to 100% of users, exactly the "
        "failure guardrails exist to catch before it reaches everyone."
    )


if __name__ == "__main__":
    main()
