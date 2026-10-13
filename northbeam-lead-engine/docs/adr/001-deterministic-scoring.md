# ADR 001 — Deterministic ICP scoring

## Status
Accepted

## Context
LLM-assisted outbound tools often let the model both write copy and decide fit. That couples hallucination risk to routing decisions and makes A/B debugging hard.

## Decision
ICP score (0–100) and tier (A/B/C) are computed only by deterministic Python against `app/config/icp.yml`. The LLM may write `fit_rationale` from facts but cannot change the numeric score.

## Consequences
- Scoring is reproducible and unit-testable (INV-6).
- Prompt injection on company pages cannot raise tier via prose (INV-5).
- Changing ICP strategy is a config/code change, not a prompt tweak.
