"""
local_vs_api.py

Compares running embeddings LOCALLY (self-hosted, like Sentence-
Transformers) versus calling an API (like OpenAI or Mistral). Neither
is universally "right" -- this file lays out the actual tradeoffs and
gives a simple decision guide.
"""


LOCAL_PROS = [
    "No data ever leaves your infrastructure -- strongest privacy guarantee.",
    "No per-token cost once the model is downloaded -- just compute.",
    "Works fully offline, no network dependency or API outage risk.",
    "Full control over model version -- it won't silently change underneath you.",
]

LOCAL_CONS = [
    "You own the infrastructure: GPUs/CPUs, scaling, uptime, monitoring.",
    "You're responsible for keeping the model updated as better ones release.",
    "Initial setup (model download, dependency management) takes real effort.",
    "Typically trails the very best hosted models on general quality benchmarks.",
]

API_PROS = [
    "Zero infrastructure to manage -- just an API call.",
    "Access to frontier-quality models without hosting them yourself.",
    "Providers handle scaling, uptime, and model improvements automatically.",
    "Fast to get started -- often a single API call away.",
]

API_CONS = [
    "Your data is sent to a third party -- a real concern for sensitive content.",
    "Ongoing per-token cost that scales with usage, sometimes unpredictably.",
    "Network latency and dependency on the provider's uptime.",
    "The provider can change pricing, deprecate models, or change behavior on you.",
]


def print_comparison():
    print("--- Local (self-hosted) ---\n")
    print("Pros:")
    for p in LOCAL_PROS:
        print(f"  + {p}")
    print("Cons:")
    for c in LOCAL_CONS:
        print(f"  - {c}")

    print("\n--- API-based ---\n")
    print("Pros:")
    for p in API_PROS:
        print(f"  + {p}")
    print("Cons:")
    for c in API_CONS:
        print(f"  - {c}")


def estimate_breakeven(num_embeddings_per_month, avg_tokens_per_embedding, api_price_per_1k_tokens, local_monthly_compute_cost):
    """
    A simple economic model: at what volume does self-hosting start
    costing less than paying per-token for an API? Below the breakeven
    point, the API is cheaper (you're not using enough volume to justify
    owning hardware). Above it, local hosting wins on raw cost -- though
    cost isn't the only factor that matters (see the qualitative tradeoffs
    above).
    """
    monthly_api_cost = (num_embeddings_per_month * avg_tokens_per_embedding / 1000) * api_price_per_1k_tokens
    return monthly_api_cost, local_monthly_compute_cost


def decision_guide():
    print("\n--- Simple decision guide ---\n")
    print(
        "Choose LOCAL when:\n"
        "  - You're handling sensitive data (health records, legal documents,\n"
        "    internal company data) that can't leave your infrastructure.\n"
        "  - Your volume is high enough that per-token API costs would be\n"
        "    substantial (see the breakeven calculation below).\n"
        "  - You need to work fully offline or in an air-gapped environment.\n\n"
        "Choose API when:\n"
        "  - You're prototyping or at low-to-moderate volume -- infrastructure\n"
        "    overhead isn't worth it yet.\n"
        "  - You want access to the highest-quality models without hosting\n"
        "    them yourself.\n"
        "  - Your team doesn't want to own ML infrastructure operations.\n"
    )


def main():
    print("=== Local vs. API-Based Embeddings ===\n")

    print_comparison()

    print("\n--- Breakeven example ---\n")
    # Using text-embedding-3-LARGE pricing here, not the ultra-cheap small
    # tier -- a more realistic case where quality requirements push you
    # toward a pricier API model, which is exactly the situation where a
    # genuine volume-based breakeven against local hosting shows up.
    scenarios = [
        ("Low volume (10K embeddings/month)", 10_000),
        ("Medium volume (5M embeddings/month)", 5_000_000),
        ("High volume (200M embeddings/month)", 200_000_000),
    ]
    api_price = 0.00013  # roughly OpenAI's large-model pricing per 1K tokens
    local_monthly_cost = 150.00  # a rough estimate for a small always-on GPU instance

    for label, volume in scenarios:
        api_cost, local_cost = estimate_breakeven(volume, avg_tokens_per_embedding=50, api_price_per_1k_tokens=api_price, local_monthly_compute_cost=local_monthly_cost)
        cheaper = "API" if api_cost < local_cost else "Local"
        print(f"{label}:")
        print(f"  API cost:   ${api_cost:.2f}/month")
        print(f"  Local cost: ${local_cost:.2f}/month (rough fixed estimate)")
        print(f"  Cheaper: {cheaper}\n")

    decision_guide()

    print(
        "The breakeven point will vary a lot based on real pricing and your "
        "actual compute costs -- the point isn't the exact numbers above, "
        "it's that this is a calculation worth actually doing for your "
        "specific workload, rather than assuming either option is always "
        "cheaper. And remember: cost is only ONE factor. Privacy "
        "requirements can make 'local' the right choice even when it costs "
        "more, and quality requirements can make 'API' the right choice "
        "even at high volume."
    )


if __name__ == "__main__":
    main()
