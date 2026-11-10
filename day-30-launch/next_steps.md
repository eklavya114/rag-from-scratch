# Next Steps

Swap the toy embeddings for a real embedding model. Every hand-built
concept vocabulary in this project is a stand-in for what a trained
embedding model does automatically, learning which words relate to
which meaning from huge amounts of real text. Day 9 covers how to
choose a real model, local or hosted, and the tradeoffs between them.
Swapping one in means replacing the `text_to_embedding` function this
project rebuilds in several places with a single real call, everything
downstream of it, the vector store, ranking, generation, keeps working
unchanged, since it was never built to depend on embeddings being toy
ones specifically.

Replace the in-memory index with a real vector database. `SimpleVectorDB`
is a Python list scored with cosine similarity, fine for a few dozen
documents and completely impractical at any real scale. Day 3's
comparison of real vector databases is the place to start choosing a
real one, and Day 10's scaling work shows what actually changes, in
latency and resource use, once the document count grows past what fits
comfortably in memory.

Connect a real language model and re-run the Day 21 evaluation. Every
generated answer in this project comes from a template filling in real
retrieved text, never from an actual language model reasoning over it.
Connecting a real model changes generation meaningfully, and the honest
next step is not to assume it is better, but to re-run Day 21's real
evaluation harness against the new generator and look at the actual
numbers, the same measure-before-trusting discipline this whole project
tried to practice throughout.

Add real monitoring and a real secrets manager. Day 24's metrics
registry and alert rules, and Day 27's secrets handling, both
demonstrate the right shape of the solution using only the standard
library. A real deployment needs the real version of each: an actual
metrics backend a team can query and alert from, and an actual secrets
manager rather than an environment variable read once at startup, both
swaps that keep the same design this project already settled on.

Get a professional security review before any public launch. Day 27's
prompt injection checks, PII redaction, and access control are real,
working demonstrations of the ideas involved, built specifically to
teach how each protection works, not to serve as a certified security
boundary. Anything handling real user data, real payment information,
or anything else genuinely sensitive needs an actual security
professional to review it before it ever reaches real users, exactly
the honest limit this project has stated from Day 27 onward and
restates clearly here at the very end.
