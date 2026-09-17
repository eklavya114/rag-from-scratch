# Glossary (for beginners)

A few terms that come up a lot when talking about RAG. Quick, plain-English definitions.

**LLM (Large Language Model)**
The AI model itself (like Claude or GPT). It generates text. On its own, it only knows what it learned during training.

**Retrieval**
The step where the system searches through documents to find ones relevant to the question, before the AI writes an answer.

**Generation**
The step where the AI actually writes the answer, usually using the retrieved documents as context.

**Embedding**
A way of turning text into a list of numbers that represents its *meaning*. Two sentences with similar meaning end up with similar numbers, even if they don't share any of the same words. This is what real RAG systems use instead of simple keyword matching.

**Vector Database**
A database built to store embeddings and quickly find the ones most similar to a given query. Popular examples: Pinecone, Weaviate, Chroma, FAISS.

**Chunking**
Before you can search a big document, you usually split it into smaller pieces ("chunks"), like paragraphs or a few sentences at a time. This makes retrieval more precise — you get back the relevant paragraph, not an entire 50-page PDF.

**Keyword Search**
Finds documents containing the exact words you searched for. Fast and simple, but misses documents that describe the same idea with different words. This is what `simple_rag.py` uses today.

**Semantic Search**
Finds documents based on *meaning* rather than exact word matches, usually powered by embeddings. If you search "car" it can still find a document about "automobile." We'll build this later in the 30 days.

**Hallucination**
When an AI confidently states something false or made up. RAG helps reduce this by grounding answers in real retrieved documents instead of pure memory.

**Context Window**
The amount of text an LLM can "see" at once when generating a response. This limits how many retrieved documents you can hand it in one go.

---

You don't need to memorize any of this today. Just skim it once, then come back whenever a term in later days feels unfamiliar.
