# Generation Best Practices

A quick reference for generation decisions once you're building a real RAG system
with an actual LLM behind it, beyond the toy examples in this folder.

## Always ground the prompt in a system-level instruction

Tell the model explicitly: use only the provided context, say when the context
isn't enough, and cite sources. Don't rely on the question alone to imply this --
a system prompt (see `prompt_engineering.py`) sets the rule once, so every answer
follows it consistently instead of depending on how a particular question happened
to be phrased.

## Match prompt style to query type

A factual question, a "give me an overview" request, and a "explain this to me"
request all deserve different prompt shapes (question-answering, summarization,
explanation). Routing to the right style produces meaningfully better answers than
using one generic prompt for everything.

## Use few-shot examples when tone or format matters

If you care about a specific answer length, citation style, or tone, showing 1-2
examples of what "good" looks like is far more reliable than describing it in
words. Models are much better at matching a pattern than following an abstract
instruction.

## Never skip source attribution

An answer without clear sourcing is a claim you either trust blindly or not at
all. Track which chunk backed which part of the answer, quote the relevant text,
and expose a confidence score (see `source_attribution.py`). This is what makes a
RAG answer verifiable instead of just another confident-sounding guess.

## Respect the context window as a hard constraint, not a suggestion

Select the most relevant material first (using the ranking you already computed),
and cut or summarize the rest deliberately (see `context_management.py`). Don't
just truncate blindly at the token limit -- that risks cutting off the middle of
the single most relevant chunk while keeping a barely-relevant one intact.

## Measure generation quality, don't just eyeball it

Check whether the answer actually addresses the question, whether its length is
appropriate, and whether it stays grounded in the sources (see
`answer_quality.py`). A simple word-overlap-based consistency check won't catch
subtle misrepresentation, but it reliably catches the worst failure mode: an
answer that invents details the sources never said.

## Express uncertainty honestly

A RAG system that sounds equally confident whether it has one perfect source or
zero relevant ones is actively misleading. Hedge low-confidence answers instead of
stating them with false authority -- and when sources contradict each other,
surface the contradiction instead of silently picking one side.

## Ask for clarification when retrieval is ambiguous

If the top few ranked results are all close in score with no clear winner, that
usually means the query itself could mean several different things. Asking a
clarifying question is often better than confidently answering the wrong
interpretation.

## Remember: generation can't fix what came before it

If chunking, embedding, retrieval, or ranking got something wrong, generation
has no way to correct for it -- it can only work with whatever context it's
handed. The best generation prompt in the world still produces a bad answer from
the wrong context. Debug the earlier pipeline stages first if answers are
consistently off.

## The one-sentence summary

Generation is where every earlier stage's work either pays off or gets exposed --
treat prompting, formatting, attribution, and quality checks as seriously as the
retrieval and ranking that feeds it.
