"""
config.py

Every setting the complete project needs, in one place. A scattered
config, one value defined here, a slightly different copy there, is how
two parts of a system end up quietly disagreeing about something as
basic as how many results to retrieve. One Config object, validated once
at startup, is what Day 22 already established for the production
service, and the whole project follows that same discipline here.
"""

import os
from dataclasses import dataclass, field

DEMO_API_KEY = "demo-key-do-not-use-in-real-deployments"


@dataclass
class Config:
    top_k: int = 3
    rank_weights: dict = field(default_factory=lambda: {"similarity": 0.5, "recency": 0.3, "quality": 0.2})
    cache_size: int = 100
    max_query_length: int = 500
    rate_limit_per_minute: int = 10
    # Read from the environment, with a clearly labeled DEMO fallback, so
    # this project never requires a real secret to run, while still
    # following the same pattern a real deployment would use (Day 27's
    # secrets_handling.py covers this in more depth).
    api_key: str = field(default_factory=lambda: os.environ.get("RAG_API_KEY", DEMO_API_KEY))

    def validate(self):
        """Rejects settings that would make the system behave in a confusing or broken way, the same fail-loud-at-startup discipline Day 22's Config used."""
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

        if not isinstance(self.rate_limit_per_minute, int) or self.rate_limit_per_minute <= 0:
            errors.append(f"rate_limit_per_minute must be a positive integer, got {self.rate_limit_per_minute!r}.")

        if not self.api_key:
            errors.append("api_key must not be empty.")

        if errors:
            raise ValueError("Invalid config:\n  " + "\n  ".join(errors))

        return True


def main():
    print("=== Config ===\n")

    print("--- A valid config ---")
    good_config = Config()
    good_config.validate()
    print(f"top_k={good_config.top_k}, cache_size={good_config.cache_size}, "
          f"max_query_length={good_config.max_query_length}, "
          f"rate_limit_per_minute={good_config.rate_limit_per_minute}")
    print(f"api_key (demo): {good_config.api_key}")
    print("Validated: ok\n")

    print("--- An invalid config (top_k=0, negative cache_size) ---")
    bad_config = Config(top_k=0, cache_size=-10)
    try:
        bad_config.validate()
        print("Validated: ok (this should not print)")
    except ValueError as e:
        print(f"Validation correctly rejected it:\n{e}")

    print(
        "\nWhy settings live in one place: every other file in this "
        "project, pipeline.py, service.py, evaluate.py, imports Config "
        "from here rather than hardcoding its own copy of top_k or "
        "max_query_length. One validated object means every part of the "
        "system is guaranteed to agree on these values, and a bad value "
        "is caught once, at startup, instead of causing a confusing "
        "mismatch discovered later."
    )


if __name__ == "__main__":
    main()
