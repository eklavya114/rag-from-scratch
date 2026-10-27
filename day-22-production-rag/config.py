"""
config.py

Every setting the service cares about lives in one place. Scattering
settings across files makes it hard to know what is actually
configurable, and makes it easy for two parts of the code to disagree
about a value without anyone noticing. One dataclass, with a validate()
method, means bad settings get caught at startup, not discovered later
as a mysterious runtime bug.
"""

from dataclasses import dataclass, field


@dataclass
class Config:
    top_k: int = 3
    rank_weights: dict = field(default_factory=lambda: {"similarity": 0.5, "recency": 0.3, "quality": 0.2})
    cache_size: int = 100
    max_query_length: int = 500
    # A SOFT limit: stages are timed and the total is compared against
    # this value for logging and alerting purposes. Nothing here actually
    # cancels a running stage with threads or a timeout mechanism, since
    # that adds real complexity for a toy, single-threaded service. A
    # slow request still finishes, it just gets flagged as having gone
    # over budget.
    timeout_budget_ms: float = 200.0

    def validate(self):
        """
        Rejects settings that would make the service behave in a
        confusing or broken way. Called once at startup, so a bad config
        fails loudly and immediately instead of causing a strange bug
        three stages deep into a request.
        """
        errors = []

        if not isinstance(self.top_k, int) or self.top_k <= 0:
            errors.append(f"top_k must be a positive integer, got {self.top_k!r}.")

        if not isinstance(self.rank_weights, dict) or not self.rank_weights:
            errors.append("rank_weights must be a non-empty dict.")
        else:
            total_weight = sum(self.rank_weights.values())
            if abs(total_weight - 1.0) > 1e-6:
                errors.append(f"rank_weights must sum to 1.0, got {total_weight}.")

        if not isinstance(self.cache_size, int) or self.cache_size < 0:
            errors.append(f"cache_size must be a non-negative integer, got {self.cache_size!r}.")

        if not isinstance(self.max_query_length, int) or self.max_query_length <= 0:
            errors.append(f"max_query_length must be a positive integer, got {self.max_query_length!r}.")

        if not isinstance(self.timeout_budget_ms, (int, float)) or self.timeout_budget_ms <= 0:
            errors.append(f"timeout_budget_ms must be a positive number, got {self.timeout_budget_ms!r}.")

        if errors:
            raise ValueError("Invalid config:\n  " + "\n  ".join(errors))

        return True


def main():
    print("=== Config Validation ===\n")

    print("--- A valid config ---")
    good_config = Config()
    good_config.validate()
    print(f"top_k={good_config.top_k}, rank_weights={good_config.rank_weights}, "
          f"cache_size={good_config.cache_size}, max_query_length={good_config.max_query_length}, "
          f"timeout_budget_ms={good_config.timeout_budget_ms}")
    print("Validated: ok\n")

    print("--- An invalid config (top_k=0, negative cache_size) ---")
    bad_config = Config(top_k=0, cache_size=-10)
    try:
        bad_config.validate()
        print("Validated: ok (this should not print)")
    except ValueError as e:
        print(f"Validation correctly rejected it:\n{e}")

    print(
        "\nWhy settings live in one place: a top_k used in one spot and a "
        "different top_k used somewhere else is the kind of bug that only "
        "shows up as 'the numbers don't match' days later. One Config "
        "object, validated once at startup, means every part of the "
        "service reads the exact same values and a bad value is caught "
        "before a single request is ever served."
    )


if __name__ == "__main__":
    main()
