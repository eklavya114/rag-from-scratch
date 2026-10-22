"""
react_with_rag.py

Plugs the REAL Day 5 retriever and Day 6 ranker into the ReAct loop as
a single "search" tool. The scripted fake LLM searches first, reads
the (real) retrieved-and-ranked result as its Observation, and only
then writes its Final Answer -- showing concretely how retrieval
becomes just another Observation in the ReAct loop, not a separate
mechanism bolted on beside it.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
from tool_registry import ToolRegistry  # Day 15
from tool_builder import build_tool_from_function  # Day 16
from basic_retriever import Retriever, DOCUMENTS                  # Days 1-5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6

from react_parser import parse_react_text


class RagSearchTool:
    """Wraps the real Day 5 retriever + Day 6 ranker as a single callable -- this becomes the ReAct loop's 'search' Action."""

    def __init__(self):
        self.retriever = Retriever()
        self.retriever.index_documents(DOCUMENTS)
        self.ranker = PracticalRanker(metadata=DOCUMENT_METADATA)

    def search(self, query):
        """Searches the indexed documents and returns the top-ranked snippet as the ReAct Observation."""
        retrieved = self.retriever.retrieve(query, top_k=3)
        ranked = self.ranker.rank(retrieved)
        if not ranked:
            return {"ok": False, "error": "No relevant documents found."}
        top = ranked[0]
        return {"ok": True, "source": top["metadata"]["doc_id"], "text": top["metadata"]["text"]}


def fake_llm_react_step(history, step_number):
    """STAND-IN FOR A REAL LLM: searches first, then reads the (real) retrieved Observation before writing a Final Answer -- scripted so the loop is deterministic and needs no API key."""
    if step_number == 1:
        return "Thought: I don't know this off the top of my head -- I should search the indexed documents first.\nAction: search\nAction Input: What is RAG?"

    if step_number == 2:
        observation = history[-1]["observation"]
        if observation.get("ok"):
            return f"Thought: The search returned a grounded passage I can base my answer on.\nFinal Answer: {observation['text']}"
        return "Thought: The search found nothing useful.\nFinal Answer: I couldn't find relevant information to answer this."

    return "Thought: Wrapping up.\nFinal Answer: Unable to reach a confident answer."


def run_react_with_rag(registry, question, max_steps=4):
    print(f"Question: {question}\n")
    history = []

    for step_number in range(1, max_steps + 1):
        raw_text = fake_llm_react_step(history, step_number)
        parsed = parse_react_text(raw_text)

        print(f"Thought: {parsed.thought}")

        if parsed.final_answer:
            print(f"Final Answer: {parsed.final_answer}\n")
            return parsed.final_answer

        print(f"Action: {parsed.action}")
        print(f"Action Input: {parsed.action_input}")
        # The retrieval + ranking result becomes the Observation -- the ReAct loop
        # doesn't need to know or care that it came from a RAG pipeline rather than
        # a plain lookup tool; it's just another tool call with a structured result.
        observation = registry.call(parsed.action, parsed.action_input)
        print(f"Observation: {observation}\n")
        history.append({"thought": parsed.thought, "action": parsed.action, "observation": observation})

    return None


def main():
    print("=== ReAct with RAG ===\n")

    rag_tool = RagSearchTool()
    registry = ToolRegistry()
    build_tool_from_function(registry, rag_tool.search)

    answer = run_react_with_rag(registry, "What is RAG?")

    print(f"Final answer: {answer}")
    print(
        "\nNotice retrieval never needed special handling in the loop: once "
        "wrapped as a tool, the Day 5/6 pipeline's output is just another "
        "Observation the agent reads before deciding what to say -- the "
        "same shape as every other tool call in this folder, grounded in "
        "real indexed text instead of a scripted fact."
    )


if __name__ == "__main__":
    main()
