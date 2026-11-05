"""
when_to_fine_tune.py

This file is written for reading, nothing here needs to run. It explains
when fine-tuning a REAL model is actually worth the cost, building
directly on Day 9's coverage of choosing real embedding models, and when
a simpler fix solves the same problem for far less money and risk.
"""

WHEN_IT_IS_WORTH_IT = """
WHEN FINE-TUNING A REAL MODEL IS WORTH IT

- LARGE VOLUME: enough real usage that a small percentage improvement
  translates into a meaningful amount of better outcomes, a handful of
  queries a day rarely justifies the setup cost.

- A STABLE DOMAIN: the vocabulary, the kinds of questions asked, and
  the correct answers do not change drastically week to week. Fine-
  tuning captures a snapshot of a domain, if that domain is actively
  shifting, the fine-tuned model goes stale quickly.

- CLEAR LABELED DATA: real examples of inputs and the outputs you
  actually wanted, at a scale large enough to train on, not a handful
  of anecdotes. Label quality and quantity are usually the actual
  bottleneck, not the fine-tuning process itself.

- A MEASURED GAP: a real, quantified difference between what a generic
  model currently does and what the domain actually needs, the same
  held-out, honest measurement this folder's held_out_evaluation.py
  demonstrated on a toy scale. Fine-tuning without first measuring a
  real gap is solving a problem you have not actually confirmed exists.
"""

WHEN_IT_IS_NOT_WORTH_IT = """
WHEN FINE-TUNING A REAL MODEL IS NOT WORTH IT

- SMALL DATA: a few dozen or even a few hundred labeled examples is
  usually not enough to meaningfully move a large model without a real
  risk of overfitting to those exact examples, this project's own
  overfitting_check.py showed that risk clearly, even on a tiny toy
  adaptation.

- A CHANGING DOMAIN: if the vocabulary or the correct answers shift
  every few weeks, a fine-tuned snapshot is out of date almost as soon
  as it ships, and needs to be redone on a cadence that may not be
  sustainable.

- A BETTER PROMPT OR BETTER RETRIEVAL ALREADY FIXES IT: often the real
  problem is that the right information was never given to the model
  in the first place, not that the model fundamentally misunderstands
  the domain. Improving retrieval (better documents, better ranking, a
  bigger or better-curated index) or simply rewriting the prompt
  template is usually far cheaper to try first, and solves a surprising
  number of cases that look, at first glance, like they need fine-
  tuning.
"""

REAL_COSTS = """
THE REAL COSTS OF FINE-TUNING

- LABELING: collecting enough high-quality labeled examples is almost
  always the slowest, most expensive part, often more expensive than
  the actual training run.

- COMPUTE: training (and especially retraining, as the domain or the
  base model changes) costs real money and real time, scaling with how
  large the model and the dataset are.

- MAINTENANCE: a fine-tuned model is now an ADDITIONAL asset to keep
  up to date, retrain as the domain shifts, and monitor for regressions
  separately from whatever base model it started from.

- RISK OF FORGETTING GENERAL KNOWLEDGE: fine-tuning too aggressively on
  a narrow domain can make a model WORSE at everything outside that
  domain, sometimes even at parts of the domain the fine-tuning data
  did not happen to cover. A model fine-tuned hard on shipping and
  refunds might get noticeably worse at ordinary conversation or
  general reasoning it previously handled fine.
"""


def main():
    print("=== When to Fine-Tune (reading material, nothing here runs) ===\n")
    print(WHEN_IT_IS_WORTH_IT)
    print(WHEN_IT_IS_NOT_WORTH_IT)
    print(REAL_COSTS)


if __name__ == "__main__":
    main()
