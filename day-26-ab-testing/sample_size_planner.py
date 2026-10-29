"""
sample_size_planner.py

Answers "how many users do I need?" BEFORE starting an experiment. The
inputs are: a baseline rate (what the current variant already achieves),
the minimum detectable effect, the smallest change actually worth caring
about, and a confidence level. Choosing the minimum detectable effect
first matters because it sets the entire scale of the experiment: a
smaller effect you want to detect requires a much larger sample, there is
no way to reliably find a tiny difference with a tiny sample, no matter
how the math is done.
"""

import math

# Standard normal z-scores for common two-sided confidence levels,
# the same values any statistics table would give. 95% confidence is the
# most common default; included here instead of computed, since inverting
# the normal CDF needs more than math.erfc alone provides, and these
# fixed points are all a sample size calculator actually needs.
Z_FOR_CONFIDENCE = {
    0.90: 1.645,
    0.95: 1.960,
    0.99: 2.576,
}

Z_FOR_POWER_80_PERCENT = 0.842  # the standard z-score for 80% statistical power, used alongside the confidence level


def required_sample_size_per_arm(baseline_rate, minimum_detectable_effect, confidence=0.95):
    """
    Computes the minimum number of users needed PER ARM (so the total
    experiment needs roughly double this) to reliably detect a change of
    at least minimum_detectable_effect in a proportion starting at
    baseline_rate, at the given confidence level. Uses the standard
    formula for a two-proportion test: more samples are needed as the
    effect you're trying to detect shrinks, and as the baseline rate
    moves away from the extremes (0% or 100%) toward 50%, where
    variance is highest.
    """
    if confidence not in Z_FOR_CONFIDENCE:
        raise ValueError(f"confidence must be one of {sorted(Z_FOR_CONFIDENCE)}, got {confidence}.")

    z_alpha = Z_FOR_CONFIDENCE[confidence]
    z_beta = Z_FOR_POWER_80_PERCENT

    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    p_bar = (p1 + p2) / 2

    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2

    return math.ceil(numerator / denominator)


def main():
    print("=== Sample Size Planner ===\n")

    scenarios = [
        {"name": "Small effect, 95% confidence", "baseline": 0.50, "mde": 0.03, "confidence": 0.95},
        {"name": "Medium effect, 95% confidence", "baseline": 0.50, "mde": 0.10, "confidence": 0.95},
        {"name": "Medium effect, 99% confidence", "baseline": 0.50, "mde": 0.10, "confidence": 0.99},
    ]

    print(f"{'scenario':<34}{'baseline':<12}{'mde':<10}{'confidence':<14}{'users per arm':<14}")
    print("-" * 84)
    for scenario in scenarios:
        n = required_sample_size_per_arm(scenario["baseline"], scenario["mde"], scenario["confidence"])
        print(f"{scenario['name']:<34}{scenario['baseline']:<12.0%}{scenario['mde']:<10.0%}"
              f"{scenario['confidence']:<14.0%}{n:<14}")

    print(
        "\nWhy choosing the minimum detectable effect comes BEFORE "
        "starting an experiment: the first scenario above, trying to "
        "detect a 3 percentage point change, needs over 10 times as many "
        "users per arm as detecting a 10 point change at the same "
        "confidence level, even though both start from the same 50% "
        "baseline. If you start an experiment without deciding in "
        "advance how small a change is actually worth catching, there is "
        "no way to know whether your sample size will ever be enough, "
        "and no principled way to decide when to stop collecting data, "
        "which is exactly the gap that leads to peeking early and "
        "stopping on a lucky result."
    )


if __name__ == "__main__":
    main()
