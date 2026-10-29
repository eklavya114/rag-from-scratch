"""
significance_check.py

A two-proportion z-test, implemented with only the standard library's
math module, no scipy or any statistics package. Answers the question a
raw percentage difference cannot answer on its own: is this difference
large enough, given how much data was collected, to actually trust, or
small enough that it could plausibly have happened by chance even if the
two variants were truly identical.
"""

import math


def two_proportion_z_test(successes_a, n_a, successes_b, n_b):
    """
    Computes a z-score for the difference between two observed
    proportions (for example, helpfulness rate for variant A vs B), using
    a pooled proportion under the null hypothesis that both variants have
    the SAME true underlying rate. A larger magnitude z-score means the
    observed difference is less likely to have happened by chance alone.
    """
    if n_a == 0 or n_b == 0:
        return None

    p_a = successes_a / n_a
    p_b = successes_b / n_b

    pooled_p = (successes_a + successes_b) / (n_a + n_b)
    pooled_variance = pooled_p * (1 - pooled_p) * (1 / n_a + 1 / n_b)

    if pooled_variance == 0:
        return None  # no variance at all (e.g. both rates are exactly 0% or 100%), a z-score is undefined

    z_score = (p_b - p_a) / math.sqrt(pooled_variance)
    return z_score


def two_sided_p_value(z_score):
    """
    Converts a z-score into a two-sided p-value using math.erfc (the
    complementary error function), the standard way to compute a normal
    distribution's tail probability without needing scipy. A p-value is
    the probability of seeing a difference at least this extreme, if
    there were actually NO real difference between the two variants.
    """
    return math.erfc(abs(z_score) / math.sqrt(2))


SIGNIFICANCE_THRESHOLD = 0.05


def evaluate_experiment(successes_a, n_a, successes_b, n_b, threshold=SIGNIFICANCE_THRESHOLD):
    """Runs the full check and returns a plain-English verdict alongside the raw numbers."""
    z_score = two_proportion_z_test(successes_a, n_a, successes_b, n_b)
    if z_score is None:
        return {"z_score": None, "p_value": None, "verdict": "Not enough data to compute a meaningful test."}

    p_value = two_sided_p_value(z_score)
    rate_a = successes_a / n_a
    rate_b = successes_b / n_b

    if p_value < threshold:
        direction = "higher" if rate_b > rate_a else "lower"
        verdict = f"The difference is real: variant B's rate is reliably {direction} than variant A's (p={p_value:.4f})."
    else:
        verdict = f"Not enough evidence yet: this difference could plausibly be chance (p={p_value:.4f}), collect more data before deciding."

    return {"z_score": z_score, "p_value": p_value, "rate_a": rate_a, "rate_b": rate_b, "verdict": verdict}


def main():
    print("=== Significance Check ===\n")

    print("--- A small experiment: 30 users per arm ---")
    # A real-looking but small gap: 50% vs 63%, the kind of difference
    # that LOOKS meaningful on a small sample but is not yet proven.
    small_result = evaluate_experiment(successes_a=15, n_a=30, successes_b=19, n_b=30)
    print(f"A: 15/30 (50.0%), B: 19/30 (63.3%)")
    print(f"z-score: {small_result['z_score']:.3f}")
    print(f"p-value: {small_result['p_value']:.4f}")
    print(f"Verdict: {small_result['verdict']}\n")

    print("--- A larger experiment: 500 users per arm, same percentage difference ---")
    large_result = evaluate_experiment(successes_a=250, n_a=500, successes_b=316, n_b=500)
    print(f"A: 250/500 (50.0%), B: 316/500 (63.2%)")
    print(f"z-score: {large_result['z_score']:.3f}")
    print(f"p-value: {large_result['p_value']:.6f}")
    print(f"Verdict: {large_result['verdict']}\n")

    print(
        "Why sample size matters, and why peeking early inflates false "
        "wins: the SAME roughly 13 percentage point gap produced an "
        "inconclusive result at 30 users per arm, and a clearly "
        "conclusive one at 500 per arm. A small sample simply does not "
        "contain enough information to rule out chance, even when the "
        "observed gap looks identical to a larger, real one. 'Peeking' "
        "means checking results early and stopping the moment they look "
        "favorable, if you check a noisy small-sample result repeatedly "
        "and stop as soon as it happens to clear your threshold by luck, "
        "you are far more likely to declare a win that is not actually "
        "real than if you had committed to one check after collecting a "
        "properly planned amount of data (see sample_size_planner.py)."
    )


if __name__ == "__main__":
    main()
