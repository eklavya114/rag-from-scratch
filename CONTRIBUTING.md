# Contributing

Thanks for taking a look at this project. It is a 30 day course that builds a RAG system from scratch, so most contributions will be small fixes, clearer explanations, or careful additions to an existing day, rather than entirely new features.

## Running the project

You can run the whole system with two commands from the repository root.

```bash
python day-29-complete-system/main.py
python day-29-complete-system/tests.py
```

The first builds the complete system and answers a few sample questions. The second runs the test suite that should always pass. If you change anything, run both before you open a pull request.

## The pattern every day follows

Each day folder, from `day-01-rag-basics` through `day-30-launch`, follows the same shape. There is a README.md explaining the day's topic in plain language, a BEST_PRACTICES.md with a few short notes on what matters and why, one or more runnable Python scripts, and a notebook.ipynb that walks through the day end to end. If you add a new day or extend an existing one, please follow this same shape so the project stays consistent.

## The rules

This project uses only the Python standard library. Please do not add a dependency on a third party package or a vendor SDK, even a small one, since the whole point of the project is that every piece can be read and run without installing anything extra.

Later days should import real code from earlier days instead of copying it. If you need something from an earlier day, add it to your script's imports rather than pasting a modified version of it. This keeps a bug fix in one place fixed everywhere it is used.

Never commit a real API key, a real secret, or any personal data, even in a test file or an example. This project runs entirely offline and should stay that way.

New text you write for this project, in code comments, READMEs, or anywhere else, should not use em dashes. Commas, periods, or colons work fine instead.

## Proposing a change

The easiest way to propose a change is to open an issue describing what you would like to fix or add, or to open a pull request directly if you already have the change ready. Please keep pull requests small and focused on one thing at a time, and say clearly in the description which day folder the change touches. A small, well scoped change is much easier to review than a large one that touches many days at once.
