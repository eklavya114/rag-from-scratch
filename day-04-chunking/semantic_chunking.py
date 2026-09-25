"""
semantic_chunking.py

All the chunking methods so far split text mechanically: by character
count, word count, or punctuation. None of them ask "are these two
sentences actually about the same thing?"

Semantic chunking does. It uses embeddings (Day 2) to measure how similar
consecutive sentences are, and only starts a new chunk when the topic
actually seems to shift. Related ideas stay together, even if that means
chunks end up different sizes.
"""

import math
import re


def cosine_similarity(vector_a, vector_b):
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    mag_a = math.sqrt(sum(a * a for a in vector_a))
    mag_b = math.sqrt(sum(b * b for b in vector_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# Same concept-based fake embedding approach from Day 2 and Day 3: score
# each sentence against a small set of hand-picked concepts (including
# synonyms), which stands in for a real trained embedding model.
CONCEPTS = {
    "rag_intro":     ["rag", "retrieval-augmented", "generation", "technique", "combines", "search",
                       "approach", "retrieves", "retrieval", "generating", "response", "answers"],
    "limitations":   ["limitations", "cutoff", "date", "trained", "private", "data", "knowledge",
                       "training", "collected", "access"],
    "pipeline":      ["pipeline", "steps", "documents", "chunks", "embeddings", "searches", "handed",
                       "split", "turned", "relevant", "question"],
    "chunking_topic": ["chunking", "overlooked", "impact", "quality", "big", "small", "context",
                        "irrelevant", "information", "useful", "enough"],
}


def sentence_to_embedding(sentence):
    words = set(w.strip("?.,!").lower() for w in sentence.split())
    return [
        float(sum(1 for word in words if word in concept_words))
        for concept_words in CONCEPTS.values()
    ]


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.replace("\n", " ").strip())
    return [s for s in sentences if s]


def semantic_chunk(text, similarity_threshold=0.3):
    """
    Groups consecutive sentences into a chunk as long as each new
    sentence is similar enough to the current chunk's topic. Once a
    sentence's similarity drops below the threshold, that's treated as
    a topic shift, and a new chunk starts.

    This means chunk boundaries land where the TOPIC changes, not where
    an arbitrary word or character count runs out -- the whole point of
    semantic chunking.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks = []
    current_chunk_sentences = [sentences[0]]
    current_chunk_embedding = sentence_to_embedding(sentences[0])

    for sentence in sentences[1:]:
        sentence_embedding = sentence_to_embedding(sentence)
        similarity = cosine_similarity(current_chunk_embedding, sentence_embedding)

        if similarity >= similarity_threshold:
            # Similar enough to the current topic -- keep it in this chunk,
            # and blend its embedding into the chunk's running "average"
            # topic so the chunk's theme can drift gradually if needed.
            current_chunk_sentences.append(sentence)
            current_chunk_embedding = [
                (a + b) / 2 for a, b in zip(current_chunk_embedding, sentence_embedding)
            ]
        else:
            # Topic shifted -- close out the current chunk and start a
            # fresh one with this sentence.
            chunks.append(" ".join(current_chunk_sentences))
            current_chunk_sentences = [sentence]
            current_chunk_embedding = sentence_embedding

    chunks.append(" ".join(current_chunk_sentences))
    return chunks


SAMPLE_TEXT = """
RAG stands for Retrieval-Augmented Generation. It is a technique that combines
search with text generation to produce better answers. This approach retrieves
relevant information before generating a response.

Language models have knowledge cutoff dates. They don't know about anything that
happened after their training data was collected. They also lack access to private
data unless it's explicitly provided to them.

A RAG pipeline has three main steps. Documents are split into chunks and turned into
embeddings. The system searches for relevant chunks when a question comes in. The
relevant chunks are then handed to a language model to generate the final answer.

Chunking is often overlooked in RAG pipelines. It has a bigger impact on quality than
people expect. Chunks that are too big contain irrelevant information. Chunks that
are too small lack enough context to be useful.
""".strip()


def main():
    print("=== Semantic Chunking Demo ===\n")

    chunks = semantic_chunk(SAMPLE_TEXT, similarity_threshold=0.3)

    print(f"Produced {len(chunks)} semantic chunks from {len(split_into_sentences(SAMPLE_TEXT))} sentences:\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Chunk {i} ---")
        print(chunk)
        print()

    print(
        "Notice each chunk stayed on one topic (what RAG is, why it's needed, "
        "the pipeline steps, why chunking matters) even though sentence counts "
        "per chunk vary. A mechanical 'group every N sentences' approach "
        "wouldn't guarantee that -- it could easily split a topic in half or "
        "merge two unrelated topics into one chunk, just based on where the "
        "sentence count happened to land."
    )


if __name__ == "__main__":
    main()
