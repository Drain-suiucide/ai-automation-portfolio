# ADR 004 — Fact grounding

## Status
Accepted

## Context
Personalized outbound fails trust when the model invents company details. Citations in chat products differ: here sources are fetched company pages, not a knowledge base.

## Decision
Facts are `{id, type, value, source_url, snippet, fetched_at}`. Personalized draft sentences must list `fact_ids`. A grounding validator checks ID existence and token overlap with snippets; failure falls back to a neutral template. Unsupported claims cannot be sent (INV-4).

## Consequences
- Enrichment quality bounds personalization quality.
- Fake LLM in demos always cites extracted facts.
- Optional LLM-as-judge can tighten heuristics later without changing the invariant.
