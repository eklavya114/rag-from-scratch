# Changelog

## v1.0.0 (first release)

A complete RAG system built from scratch over 30 days, using only the
Python standard library. No API keys, no GPU, and no internet
connection are needed to run any part of it.

### Week 1: Foundations, retrieval, ranking, generation (Days 1 to 7)

- Day 1: Built the first basic RAG system using keyword search.
- Day 2: Turned text into toy embeddings and compared them to keyword matching.
- Day 3: Stored embeddings in a simple vector database and searched it.
- Day 4: Split documents into chunks using several real strategies.
- Day 5: Tied chunking, embeddings, and the vector database into one retriever.
- Day 6: Ranked retrieved chunks using similarity, recency, and quality.
- Day 7: Generated readable, sourced answers from ranked chunks.

### Week 2: Evaluation, scaling, context, query rewriting, hallucinations, caching (Days 8 to 14)

- Day 8: Measured retrieval quality with real precision, recall, NDCG, and MRR.
- Day 9: Compared real embedding models and when fine-tuning one makes sense.
- Day 10: Benchmarked the pipeline from 100 to 100,000 documents.
- Day 11: Managed context windows with a budget calculator and density metric.
- Day 12: Rewrote queries to handle decomposition, expansion, and ambiguity.
- Day 13: Reduced hallucinations and measured factuality honestly.
- Day 14: Built multi-level caching and measured real speedups.

### Week 3: Agents, tools, ReAct, memory, function calling, planning, agent evaluation (Days 15 to 21)

- Day 15: Built the first agent that could think, decide, and act.
- Day 16: Designed well-built custom tools for an agent to call.
- Day 17: Made agent reasoning explicit with the ReAct pattern.
- Day 18: Gave agents short-term, long-term, and episodic memory.
- Day 19: Replaced free-text reasoning with structured function calling.
- Day 20: Built an agent that plans multiple steps ahead and replans on failure.
- Day 21: Measured agent performance with a real evaluation harness.

### Week 4: Production service, deployment, monitoring, edge cases, A/B testing, security, domain adaptation, complete system (Days 22 to 29)

- Day 22: Wrapped the pipeline in a production-style service with validation and caching.
- Day 23: Deployed the service as a real HTTP API with a standard library server.
- Day 24: Added metrics, alert rules, and a dashboard for real monitoring.
- Day 25: Found and fixed weird inputs, slow dependencies, and partial failures.
- Day 26: Compared two versions fairly with a real A/B test and significance check.
- Day 27: Added prompt injection checks, PII redaction, and access control.
- Day 28: Adapted the toy system to a real domain and measured it honestly.
- Day 29: Connected every piece into one complete, tested, runnable project.

### Day 30: Launch

- Verified the whole project with a real, running release checklist.
- Wrote this changelog, a front-page README, and an honest retrospective.
- Tagged this exact, verified state as v1.0.0.
