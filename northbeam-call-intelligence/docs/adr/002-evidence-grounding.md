# ADR 002: Every model claim must point at the transcript

**Status:** accepted

## Context
Language models produce plausible items that nobody said. A CRM note that says "agent promised a refund"
must be true, or it becomes a liability.

## Decision
The model is an untrusted extractor. Each action item, objection and commitment carries `evidence`
(segment ids) and a `quote` of at most 15 words. The validator keeps an item only if the segments exist,
the quote is a normalized substring of a cited segment, and, for discounts, the stated percentage is
readable in the quote itself. Competitors must appear in the transcript. Everything else is dropped and
counted (`validation.dropped`), and a visible `ungrounded_items_dropped` flag is added.
Unknown top-level keys from the model are ignored and reported.

## Consequences
- Fabricated items cannot reach the CRM (`INV-3`). `scripts/evaluate.py` injects hallucinations and checks
  that all of them are dropped.
- Recall can suffer when a model paraphrases instead of quoting; the prompt asks for verbatim quotes.
- The check is lexical. It proves the words were said, not that the model interpreted them correctly.
