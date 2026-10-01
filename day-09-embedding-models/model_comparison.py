"""
model_comparison.py

We can't call real embedding APIs in this project, so we simulate what
"different model quality" actually means: a model with a SPARSE concept
vocabulary (misses a lot of synonyms, like an under-trained or narrow
model would), a model matching Day 2's original vocabulary (our
project's baseline "medium" model), and a model with an EXPANDED
vocabulary (catches more paraphrasing, like a better-trained model
would). Then we run Day 8's real evaluation framework against each one,
so "model B is better than model A" is a measured number, not a claim.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
from basic_retriever import DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import EvaluationDataset, evaluate_retriever, print_evaluation_summary, unique_doc_ids_in_order


class SimulatedEmbeddingModel:
    """
    Stands in for a real embedding model. Each "model" is really just a
    different concept vocabulary -- a sparser vocabulary simulates a
    lower-quality model that misses more paraphrasing; a richer
    vocabulary simulates a higher-quality model that generalizes better.
    A small per-call delay simulates the real-world fact that bigger,
    higher-quality models are also usually slower.
    """

    def __init__(self, name, concepts, simulated_latency_ms, cost_per_1k_tokens):
        self.name = name
        self.concepts = concepts
        self.simulated_latency_ms = simulated_latency_ms
        self.cost_per_1k_tokens = cost_per_1k_tokens

    def embed(self, text):
        if self.simulated_latency_ms:
            time.sleep(self.simulated_latency_ms / 1000)
        words = set(w.strip("?.,!").lower() for w in text.split())
        return [float(sum(1 for w in words if w in concept_words)) for concept_words in self.concepts.values()]


def cosine_similarity(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    return dot / (ma * mb) if ma and mb else 0.0


# "Low quality": a narrow vocabulary, missing most paraphrasing words.
LOW_QUALITY_CONCEPTS = {
    "programming": ["python", "programming"],
    "retrieval": ["rag", "retrieval"],
    "search_tech": ["vector", "database", "embeddings"],
}

# "Medium quality": Day 2's original vocabulary (this project's baseline).
MEDIUM_QUALITY_CONCEPTS = {
    "programming":   ["python", "programming", "language", "syntax", "code", "scripting", "coding"],
    "data_types":    ["data", "types", "strings", "integers", "floats", "lists", "dictionaries", "tuples", "sets"],
    "retrieval":     ["rag", "retrieval", "retrieves", "generation", "lookup", "look", "fetch", "find"],
    "freshness":     ["outdated", "fresh", "private", "retrained", "matters", "specific", "old", "stale", "problem"],
    "search_tech":   ["vector", "database", "embeddings", "similarity", "search", "numerical", "meaning", "meanings"],
    "keyword_match": ["keyword", "exact", "words", "matching", "simple", "fast"],
}

# "High quality": the medium vocabulary PLUS fixes for the exact gap
# Day 8's per_query_diagnosis.py found -- "fast" no longer only means
# "keyword_match", "lookup"/"store" are properly tied to search_tech too,
# simulating a model that generalizes better across phrasings.
HIGH_QUALITY_CONCEPTS = {
    "programming":   ["python", "programming", "language", "syntax", "code", "scripting", "coding", "readable"],
    "data_types":    ["data", "types", "strings", "integers", "floats", "lists", "dictionaries", "tuples", "sets"],
    "retrieval":     ["rag", "retrieval", "retrieves", "generation", "lookup", "look", "fetch", "find", "store"],
    "freshness":     ["outdated", "fresh", "private", "retrained", "matters", "specific", "old", "stale", "problem", "give", "answers"],
    "search_tech":   ["vector", "database", "embeddings", "similarity", "search", "numerical", "meaning", "meanings", "lookup", "store", "fast"],
    "keyword_match": ["keyword", "exact", "words", "matching", "simple"],
}


MODELS = {
    "low-quality (narrow vocab)": SimulatedEmbeddingModel("low-quality", LOW_QUALITY_CONCEPTS, simulated_latency_ms=1, cost_per_1k_tokens=0.00),
    "medium-quality (Day 2 baseline)": SimulatedEmbeddingModel("medium-quality", MEDIUM_QUALITY_CONCEPTS, simulated_latency_ms=5, cost_per_1k_tokens=0.02),
    "high-quality (expanded vocab)": SimulatedEmbeddingModel("high-quality", HIGH_QUALITY_CONCEPTS, simulated_latency_ms=15, cost_per_1k_tokens=0.13),
}


def make_retrieve_fn(model, documents):
    """
    Builds a from-scratch retriever using ONE specific embedding model,
    so we can swap models in and out and measure the effect on
    retrieval quality with everything else (chunking, documents, test
    set) held constant.
    """
    index = []
    for doc in documents:
        for i, chunk in enumerate(doc["text"].split("\n\n")):
            chunk = chunk.strip()
            if not chunk:
                continue
            embedding = model.embed(doc["title"] + " " + chunk)
            index.append((embedding, {"doc_id": doc["id"], "title": doc["title"], "chunk_index": i}))

    def retrieve_fn(query, k):
        query_embedding = model.embed(query)
        scored = [(meta, cosine_similarity(query_embedding, emb)) for emb, meta in index]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [{"metadata": m, "similarity": s} for m, s in scored[:k] if s > 0]

    return retrieve_fn


class ModelComparator:
    """Runs Day 8's evaluation against several embedding models and reports results side by side."""

    def __init__(self, documents, dataset):
        self.documents = documents
        self.dataset = dataset

    def compare(self, models, k=3):
        results = {}
        for name, model in models.items():
            retrieve_fn = make_retrieve_fn(model, self.documents)
            start = time.perf_counter()
            eval_results = evaluate_retriever(retrieve_fn, self.dataset, k=k)
            elapsed = time.perf_counter() - start
            results[name] = {**eval_results, "model": model, "eval_time_s": elapsed}
        return results


def main():
    print("=== Embedding Model Comparison ===\n")

    dataset = build_manual_ground_truth_dataset()
    comparator = ModelComparator(DOCUMENTS, dataset)

    results = comparator.compare(MODELS, k=3)

    for name, r in results.items():
        print_evaluation_summary(name, r, k=3)

    print("=" * 60)
    print("\n--- Side-by-side comparison ---\n")
    header = f"{'Model':<32} | {'NDCG':>6} | {'MRR':>6} | {'MAP':>6} | {'$/1K tok':>9} | {'Latency (ms)':>12}"
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        model = r["model"]
        print(
            f"{name:<32} | {r['avg_ndcg']:>6.3f} | {r['mrr']:>6.3f} | {r['map']:>6.3f} | "
            f"{model.cost_per_1k_tokens:>9.3f} | {model.simulated_latency_ms:>12}"
        )

    best_quality = max(results, key=lambda name: results[name]["avg_ndcg"])
    cheapest = min(results, key=lambda name: results[name]["model"].cost_per_1k_tokens)

    print(f"\nBest quality (NDCG): {best_quality} ({results[best_quality]['avg_ndcg']:.3f})")
    print(f"Cheapest:            {cheapest} (${results[cheapest]['model'].cost_per_1k_tokens:.3f}/1K tokens)")

    print(
        "\nWhich model for which use case:\n"
        "- Low-quality/narrow-vocab model: fine for a quick prototype or an\n"
        "  extremely narrow, keyword-heavy domain, but it will measurably\n"
        "  miss paraphrased queries -- not safe to ship broadly.\n"
        "- Medium-quality model: a reasonable default once the gap to\n"
        "  high-quality is small relative to its lower cost and latency.\n"
        "- High-quality model: worth the extra cost specifically when\n"
        "  retrieval quality is the measured bottleneck (see Day 8's\n"
        "  per_query_diagnosis.py for how to find that out), not by default."
    )


if __name__ == "__main__":
    main()
