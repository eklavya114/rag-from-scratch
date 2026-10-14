"""
integration_with_previous_days.py

Wires an agent to the REAL Day 1-14 pipeline: the Day 5 retriever, the
Day 6 ranker, and the Day 7 generator become one of the agent's tools
(a "rag_answer" tool), alongside a plain "guess" tool that has no
access to real documents. Comparing the two shows concretely why an
agent that can call RAG is smarter than one that can't.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
from basic_retriever import Retriever, DOCUMENTS                  # Days 1-5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from simple_generator import Generator                             # Day 7

from tool_examples import create_ticket_tool, send_email_tool


class RagTool:
    """Wraps the real Day 5/6/7 pipeline as a single callable tool an agent can use -- retrieval + ranking + generation, behind one function call."""

    def __init__(self):
        self.retriever = Retriever()
        self.retriever.index_documents(DOCUMENTS)
        self.ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
        self.generator = Generator()

    def answer(self, question):
        retrieved = self.retriever.retrieve(question, top_k=5)
        ranked = self.ranker.rank(retrieved)
        return self.generator.generate_concatenation(question, ranked, max_chunks=3)


def guess_tool(question):
    """A tool with NO access to real documents -- simulates an agent that can only pattern-match on the question text, standing in for 'an agent without RAG.'"""
    return f"I'm not certain, but based on general knowledge, this is likely related to: {question.split()[-1].strip('?')}."


class RagAwareAgent:
    """
    An agent with two tools available: a plain guess, and the real RAG
    pipeline. It prefers RAG whenever the question looks like something
    the indexed documents could actually answer, and falls back to a
    guess only when RAG comes back empty -- the same "escalate only
    when needed" shape as the support agent in real_world_examples.py.
    """

    def __init__(self, rag_tool):
        self.rag_tool = rag_tool
        self.actions_taken = []

    def answer_question(self, question):
        rag_answer = self.rag_tool.answer(question)
        self.actions_taken.append({"tool": "rag_answer", "question": question})

        if "no relevant" in rag_answer.lower() or not rag_answer.strip():
            guess = guess_tool(question)
            self.actions_taken.append({"tool": "guess", "question": question})
            return guess, "fallback_guess"

        return rag_answer, "rag_answer"


def demonstrate_rag_vs_no_rag(question, rag_tool):
    print(f"Question: \"{question}\"\n")

    print("--- Without RAG (guess only) ---")
    guess = guess_tool(question)
    print(f"  {guess}\n")

    print("--- With RAG (agent calls the real Day 5/6/7 pipeline) ---")
    rag_answer = rag_tool.answer(question)
    print(f"  {rag_answer}")


def demonstrate_agent_taking_action(agent):
    """
    Shows the agent not just answering, but ACTING on what RAG told it
    -- the actual point of Week 3: RAG tells the agent what's true,
    the agent decides what to DO about it.
    """
    question = "What is RAG?"
    answer, path = agent.answer_question(question)
    print(f"Agent answered via '{path}': {answer}\n")

    print("Agent decides this answer is useful enough to share proactively:")
    send_email_tool("student@example.com", "Answer to your question about RAG", answer)
    ticket = create_ticket_tool("Follow-up: send detailed RAG explainer", priority="low")
    print(f"  {ticket}")


def main():
    print("=== Agent + RAG Integration ===\n")

    rag_tool = RagTool()

    demonstrate_rag_vs_no_rag("What is RAG?", rag_tool)

    print("\n" + "=" * 60 + "\n")

    agent = RagAwareAgent(rag_tool)
    demonstrate_agent_taking_action(agent)

    print(f"\nActions the agent took this run: {len(agent.actions_taken)}")
    for action in agent.actions_taken:
        print(f"  {action}")

    print(
        "\nThe point: the guess-only tool can only pattern-match on the "
        "question's own wording, with no access to any real information. "
        "The RAG tool retrieves and ranks ACTUAL indexed documents before "
        "generating an answer -- grounded, not guessed. And once the agent "
        "has that grounded answer, it doesn't just print it: it decides "
        "what to DO next (send an email, open a follow-up ticket), which "
        "is the one capability RAG alone never had."
    )


if __name__ == "__main__":
    main()
