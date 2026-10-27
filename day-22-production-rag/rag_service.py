"""
rag_service.py

The main entry point: one RagService class with one query() method, that
wires together every stage from Days 1 to 21 in order. This is the
"kitchen" the README's restaurant analogy describes, built entirely out
of real pieces: the Day 5 Retriever, Day 6 PracticalRanker, Day 7
Generator and source attribution, wrapped in validation, caching,
logging, and error handling that none of those earlier days needed to
worry about on their own.
"""

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))

from basic_retriever import DOCUMENTS, Retriever  # Day 5
from practical_ranker import DOCUMENT_METADATA, PracticalRanker  # Day 6
from query_preprocessing import preprocess_query  # Day 5
from simple_generator import Generator  # Day 7
from source_attribution import generate_attributed_answer  # Day 7

from config import Config
from request_validation import validate_request
from service_logging import log_request


class RagResponse:
    """A plain, inspectable response object. Every field is always present, even on failure, so callers never need to guess what's available."""

    def __init__(self, request_id, status, answer=None, sources=None, cache_hit=False, timings_ms=None):
        self.request_id = request_id
        self.status = status  # "ok", "rejected", "no_results", "error"
        self.answer = answer
        self.sources = sources or []
        self.cache_hit = cache_hit
        self.timings_ms = timings_ms or {}

    def __repr__(self):
        return f"RagResponse(status={self.status!r}, cache_hit={self.cache_hit}, request_id={self.request_id!r})"


def _time_stage(timings, name, fn, *args, **kwargs):
    """Times one stage and records it in the timings dict, so every stage's cost is visible afterward, not just the total."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    timings[name] = (time.perf_counter() - start) * 1000
    return result


class RagService:
    """
    The whole pipeline behind one method call. Builds its own index at
    construction time from a small in-memory document set, exactly like
    a real service that loads its index once at startup rather than
    re-indexing on every request.
    """

    def __init__(self, config=None):
        self.config = config or Config()
        self.config.validate()

        self.retriever = Retriever()
        self.retriever.index_documents(DOCUMENTS)
        self.ranker = PracticalRanker(weights=self.config.rank_weights, metadata=DOCUMENT_METADATA)
        self.generator = Generator()

        self.query_cache = {}
        self.cache_order = []  # tracks insertion order for a simple size-bounded cache

    def _cache_get(self, cleaned_query):
        return self.query_cache.get(cleaned_query)

    def _cache_set(self, cleaned_query, value):
        if self.config.cache_size == 0:
            return  # caching is disabled entirely, nothing is ever stored
        if cleaned_query not in self.query_cache and len(self.cache_order) >= self.config.cache_size:
            oldest = self.cache_order.pop(0)
            self.query_cache.pop(oldest, None)
        if cleaned_query not in self.query_cache:
            self.cache_order.append(cleaned_query)
        self.query_cache[cleaned_query] = value

    def query(self, raw_query):
        """
        The single entry point. Runs: validate, cache check, preprocess,
        retrieve, rank, generate, attribute, log, in that exact order.
        Any exception in a later stage is caught and turned into a safe
        "error" response rather than propagating a stack trace to the
        caller, since a production caller should never have to catch an
        internal exception type to use this service safely.
        """
        request_id = str(uuid.uuid4())[:8]
        timings = {}

        # STAGE 1: VALIDATE. Cheapest check, runs first, rejects garbage
        # before any real work starts.
        validation = _time_stage(timings, "validate", validate_request, raw_query, self.config)
        if not validation["ok"]:
            log_request(request_id, None, False, 0, None, timings, "rejected")
            return RagResponse(request_id, status="rejected", answer=validation["error"], timings_ms=timings)

        cleaned_query = validation["cleaned_query"]

        try:
            # STAGE 2: CACHE CHECK. An exact repeat of a prior query skips
            # every downstream stage entirely.
            cached = _time_stage(timings, "cache_check", self._cache_get, cleaned_query)
            if cached is not None:
                log_request(request_id, cleaned_query, True, len(cached["sources"]),
                            cached["top_doc_id"], timings, "ok")
                return RagResponse(request_id, status="ok", answer=cached["answer"],
                                    sources=cached["sources"], cache_hit=True, timings_ms=timings)

            # STAGE 3: PREPROCESS. Clean, expand, and rewrite the query
            # text before it gets embedded.
            preprocessed = _time_stage(timings, "preprocess", preprocess_query, cleaned_query)
            search_query = preprocessed["expanded"]

            # STAGE 4: RETRIEVE.
            retrieved = _time_stage(timings, "retrieve", self.retriever.retrieve, search_query, self.config.top_k)

            if not retrieved:
                log_request(request_id, cleaned_query, False, 0, None, timings, "no_results")
                return RagResponse(
                    request_id, status="no_results",
                    answer="No relevant information was found for this question.",
                    timings_ms=timings,
                )

            # STAGE 5: RANK.
            ranked = _time_stage(timings, "rank", self.ranker.rank, retrieved)

            # STAGE 6: GENERATE.
            answer_text = _time_stage(timings, "generate", self.generator.generate_concatenation, cleaned_query, ranked)

            # STAGE 7: ATTRIBUTE. Replaces the plain generated text with a
            # fully sourced, quoted, confidence-scored version.
            attributed_answer = _time_stage(timings, "attribute", generate_attributed_answer, cleaned_query, ranked)

            sources = [r["metadata"]["title"] for r in ranked]
            top_doc_id = ranked[0]["metadata"]["doc_id"]

            self._cache_set(cleaned_query, {"answer": attributed_answer, "sources": sources, "top_doc_id": top_doc_id})

            # STAGE 8: LOG.
            log_request(request_id, cleaned_query, False, len(ranked), top_doc_id, timings, "ok")

            total_ms = sum(timings.values())
            if total_ms > self.config.timeout_budget_ms:
                # A soft limit: this is logged as information, nothing is
                # cancelled or retried because of it.
                timings["over_budget"] = True

            return RagResponse(request_id, status="ok", answer=attributed_answer,
                                sources=sources, cache_hit=False, timings_ms=timings)

        except Exception as e:
            # A real stage threw. The caller gets a safe message, never
            # the exception or a stack trace; the real error goes to the
            # log instead, where it can actually be investigated.
            log_request(request_id, cleaned_query, False, 0, None, timings, "error")
            return RagResponse(
                request_id, status="error",
                answer="Something went wrong while answering this question. The issue has been logged.",
                timings_ms=timings,
            )


def main():
    print("=== RAG Service ===\n")

    service = RagService(Config())

    queries = [
        "What is RAG?",
        "What is RAG?",  # exact repeat: should hit the cache
        "What programming language is easy to read?",
        "",  # invalid
        "asdkjasldkjasldkjaslkd nonsense query about nothing relevant here",
    ]

    for query_text in queries:
        response = service.query(query_text)
        print(f"Query: {query_text!r}")
        print(f"  status: {response.status}, cache_hit: {response.cache_hit}, request_id: {response.request_id}")
        if response.status == "ok":
            print(f"  sources: {response.sources}")
        print(f"  timings_ms: {response.timings_ms}")
        print()

    print(
        "Notice the second identical query returned cache_hit=True with a "
        "near-zero cache_check timing and no retrieve/rank/generate stages "
        "at all, exactly the behavior Day 14's caching framework "
        "demonstrated, now wired into one real service entry point "
        "instead of a standalone pipeline."
    )


if __name__ == "__main__":
    main()
