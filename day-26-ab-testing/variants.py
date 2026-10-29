"""
variants.py

Defines the two versions being compared. Variant A is Day 22's RagService
with its default config, the current, trusted version. Variant B changes
exactly ONE thing: top_k, from 3 to 5. Everything else, the retriever,
the ranker, the generator, the weights, stays identical between the two.

Changing only one thing at a time is what makes an A/B test's result
interpretable. If B changed top_k AND the rank weights AND the generator
all at once, and B came out ahead, there would be no way to know WHICH
of those three changes actually caused the improvement, or whether one
change helped while another quietly hurt and they happened to cancel out.
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from rag_service import RagService  # Day 22


@dataclass
class Variant:
    name: str
    description: str
    build: callable  # a zero-argument function returning a ready RagService


def build_variant_a():
    """Variant A: the current, trusted configuration. Every A/B test needs a control group running the version already known to work."""
    return RagService(Config())


def build_variant_b():
    """Variant B: the SAME service, with exactly one change: top_k raised from 3 to 5, giving the ranker more candidates to choose from per query."""
    return RagService(Config(top_k=5))


VARIANT_A = Variant(
    name="A",
    description="Current default: top_k=3",
    build=build_variant_a,
)

VARIANT_B = Variant(
    name="B",
    description="Experiment: top_k=5 (more candidates per query)",
    build=build_variant_b,
)


def main():
    print("=== Variants ===\n")

    for variant in (VARIANT_A, VARIANT_B):
        print(f"Variant {variant.name}: {variant.description}")
        service = variant.build()
        response = service.query("What is RAG?")
        print(f"  status: {response.status}")
        print(f"  sources: {response.sources}")
        print()

    print(
        "Why only one thing should change at a time: if variant B had "
        "changed top_k AND the rank weights together, and B's "
        "helpfulness rate came out higher, there would be no way to "
        "attribute that improvement to either change specifically. One "
        "of them might have actually hurt while the other helped more, "
        "cancelling out in the aggregate number, and the next 'obvious' "
        "improvement built on top of B could then repeat whichever "
        "change was actually the bad one. Changing one variable keeps "
        "the experiment's result unambiguous: whatever difference shows "
        "up between A and B can only be explained by the single thing "
        "that actually changed."
    )


if __name__ == "__main__":
    main()
