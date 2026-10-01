# Day 9: Embedding Model Selection

Days 1-8 built a complete, measurable RAG pipeline. Today we zoom into one specific
choice that shapes everything downstream: which embedding model you actually use.

## Why embedding model choice matters so much

Every single thing we've built so far -- chunking, storage, retrieval, ranking,
generation, evaluation -- operates on top of embeddings. If the embeddings are bad,
no amount of clever ranking or prompt engineering downstream can fully recover from
it. The embedding model is the foundation everything else gets built on.

It's also an easy thing to pick once, early, and never revisit. That's a mistake:
switching embedding models is often one of the highest-leverage changes you can
make to a RAG system's quality -- real teams routinely see meaningful retrieval
quality improvements just from swapping to a better-suited embedding model, with
zero changes to chunking, ranking, or prompts.

## The tradeoff: cost vs. quality vs. speed

There's no free lunch here:

- **Bigger, higher-quality models** tend to produce embeddings that capture meaning
  more precisely -- better retrieval -- but cost more per embedding and take longer
  to run.
- **Smaller, faster, cheaper models** are great for prototyping and high-volume,
  low-stakes use cases, but can miss nuance that costs you retrieval quality.
- **Local, self-hosted models** trade API cost and network latency for needing your
  own compute and maintenance.

Picking a model means deciding where on these tradeoffs your actual use case needs
to sit -- not just picking "the best one" in the abstract.

## Real embedding models that exist

- **OpenAI `text-embedding-3-small`** — fast, cheap, solid general-purpose quality.
  A common default for getting started.
- **OpenAI `text-embedding-3-large`** — higher quality, higher cost and latency.
  Worth it when retrieval quality is the bottleneck.
- **Mistral Embed** — a capable alternative with different pricing and licensing
  tradeoffs.
- **Sentence-Transformers models** (open source, e.g. `all-MiniLM-L6-v2`) — run
  locally, no API cost, full control over your data.
- **Domain-specific models** — models fine-tuned on legal, medical, or code text
  that can outperform general-purpose models squarely within their domain.

## What we're testing today

Since this project doesn't call real embedding APIs (no keys needed, same as every
other day), we simulate what "different model quality" looks like by building fake
embeddings with deliberately different levels of fidelity -- a "low-quality" model
that captures only coarse signal, and a "high-quality" model that captures more
nuance. Then we run Day 8's actual evaluation framework against each one, so the
quality difference is a measured number, not a claim.

- `model_comparison.py` — simulated models of different quality, evaluated with
  Day 8's framework.
- `quality_vs_cost.py` — the economic tradeoff, with concrete cost math for a
  given workload.
- `domain_specific_models.py` — where specialization wins and where it doesn't.
- `real_model_guide.py` — what the actual code looks like for real production
  models, without needing an API key to read it.
- `quantization_and_optimization.py` — making a chosen model cheaper to run.
- `local_vs_api.py` — the deployment tradeoff.
- `fine_tuning_basics.py` — when and how to go beyond an off-the-shelf model.
- `notebook.ipynb` — a full walkthrough tying it together.

## How to choose between them

Start by actually measuring, on your own data and your own test queries (Day 8's
evaluation framework is exactly the tool for this) -- not by reading a benchmark
leaderboard and assuming it transfers to your specific documents and questions. A
model that's "best" on a general benchmark can lose to a cheaper model on your
specific domain, and the only way to know is to run the comparison yourself.
