"""
experiment_log.py

Records every experiment's hypothesis, variants, sample sizes, metrics,
p-value, and final decision to a JSON Lines file (one JSON object per
line, append-only), the same durable-record discipline Day 20's
replanning.py and Day 21's regression_check.py applied to their own
decisions. A decision made without a written record cannot be audited
later: nobody can check what was actually measured, what threshold was
used, or why a change shipped, once the people and the context that
produced it have moved on.
"""

import json
import os
import tempfile


def log_experiment(log_path, hypothesis, variant_a_name, variant_b_name, n_a, n_b, rate_a, rate_b, p_value, decision):
    """Appends one experiment's full record as a single JSON line. Append-only, so an experiment log is a permanent history, never silently overwritten."""
    entry = {
        "hypothesis": hypothesis,
        "variant_a": variant_a_name,
        "variant_b": variant_b_name,
        "n_a": n_a,
        "n_b": n_b,
        "rate_a": rate_a,
        "rate_b": rate_b,
        "p_value": p_value,
        "decision": decision,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_experiment_log(log_path):
    """Reads every recorded experiment back, one dict per line, in the order they were logged."""
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def print_history(entries):
    for i, entry in enumerate(entries, start=1):
        print(f"[{i}] {entry['hypothesis']}")
        print(f"    {entry['variant_a']} (n={entry['n_a']}, rate={entry['rate_a']:.1%}) vs. "
              f"{entry['variant_b']} (n={entry['n_b']}, rate={entry['rate_b']:.1%})")
        print(f"    p-value: {entry['p_value']:.4f}, decision: {entry['decision']}")
        print()


def main():
    print("=== Experiment Log ===\n")

    log_path = os.path.join(tempfile.gettempdir(), "day26_experiment_log.jsonl")

    print(f"Logging experiments to a temporary file: {log_path}\n")

    log_experiment(
        log_path,
        hypothesis="Raising top_k from 3 to 5 improves helpfulness.",
        variant_a_name="A (top_k=3)",
        variant_b_name="B (top_k=5)",
        n_a=18, n_b=18, rate_a=0.889, rate_b=0.500,
        p_value=0.0243,
        decision="Rejected: B performed significantly worse, rolled back, top_k=3 kept as default.",
    )

    log_experiment(
        log_path,
        hypothesis="A new generation prompt increases helpfulness.",
        variant_a_name="A (old prompt)",
        variant_b_name="B (new prompt)",
        n_a=400, n_b=400, rate_a=0.78, rate_b=0.81,
        p_value=0.14,
        decision="Inconclusive: difference not statistically significant yet, collecting more data before deciding.",
    )

    log_experiment(
        log_path,
        hypothesis="Adjusting rank weights toward recency improves helpfulness.",
        variant_a_name="A (default weights)",
        variant_b_name="B (recency-weighted)",
        n_a=500, n_b=500, rate_a=0.75, rate_b=0.84,
        p_value=0.0008,
        decision="Accepted: B performed significantly better, rolled out via safe_rollout.py's staged plan.",
    )

    print("--- Reading the log back ---\n")
    entries = read_experiment_log(log_path)
    print(f"Found {len(entries)} recorded experiments.\n")
    print_history(entries)

    os.remove(log_path)
    print(f"Temporary log file removed: {log_path}")

    print(
        "\nWhy a decision needs a written record: 'we tried raising "
        "top_k once and it didn't work' is a much weaker statement six "
        "months later than a log entry showing the exact hypothesis, "
        "sample sizes, rates, and p-value that led to that conclusion. "
        "Without a record, nobody can tell whether a past experiment was "
        "actually well-powered, whether the same idea already failed "
        "under slightly different conditions, or whether it is worth "
        "trying again with a larger sample, every question ends up "
        "resting on someone's memory of what happened instead of on what "
        "was actually measured."
    )


if __name__ == "__main__":
    main()
