# Architecture Open Questions — Nutrition Knowledge Assistant

**Status:** Active; unresolved items are deliberate and must not be treated as implemented decisions.
**Owner:** Agent 02 with Agent 00 / designated follow-up owners
**Last updated:** 2026-11-18

This register preserves questions that materially affect implementation, safety, cost, or legal posture. The architecture chooses safe defaults where possible, while leaving decisions open when project evidence is insufficient.

## AQ-01 — WHO / USDA licensing and usage rights

- **Why it matters:** Public accessibility does not establish permission to store, transform, embed, or redistribute full text. Provenance and citation behavior depend on permitted content.
- **Options:** (a) rights-cleared full text; (b) licensed excerpts/metadata only; (c) synthetic fixtures clearly labeled as stand-ins.
- **Current recommendation:** Agent 03 must approve a source before ingestion; use labeled fixtures until rights are documented. Reject `license_status=unknown`.
- **Evidence needed:** License terms, intended-use analysis, retention/redistribution review.
- **Owner / stage:** Agent 03, before production-like corpus ingestion.

## AQ-02 — Operator authentication and exposure

- **Why it matters:** Ingestion and deactivation can alter the evidence base and should not be anonymously exposed.
- **Options:** localhost-only CLI; shared bearer token; full user/operator identity and RBAC.
- **Current recommendation:** D-014 shared `OPERATOR_API_TOKEN` for operator routes, with local-only deployment assumption; move to identity-based auth before public exposure.
- **Evidence needed:** Deployment topology and threat model for any non-local environment.
- **Owner / stage:** Agent 04/09, before external deployment.

## AQ-03 — Insufficient-evidence calibration

- **Why it matters:** An aggressive score cutoff over-refuses valid questions; a weak cutoff permits unsupported answers. Similarity is not factual confidence.
- **Options:** empty-set-only gate; calibrated relevance threshold; learned/hybrid evidence sufficiency model.
- **Current recommendation:** Ship empty evidence and citation-failure gates first; leave score threshold unset until labeled evaluation data exists. D-015 is provisional.
- **Evidence needed:** Retrieval labels, Recall@k, abstention/groundedness curves, safety-sensitive test cases.
- **Owner / stage:** Agent 06/10, after baseline corpus and evaluation set exist.

## AQ-04 — Runtime citation-support verification

- **Why it matters:** A valid chunk ID can still fail to support a claim. Treating identifier validity as entailment would overstate trust.
- **Options:** eval-only human/LLM judge; deterministic lexical/structured heuristics; runtime entailment checker.
- **Current recommendation:** D-016: validity is the MVP hard gate; support is measured in evaluation. Any runtime checker requires a later decision and failure analysis.
- **Evidence needed:** Annotated claim–evidence pairs and false-positive/negative analysis.
- **Owner / stage:** Agent 10, then Agent 07 if runtime promotion is justified.

## AQ-05 — Safety component placement and failure policy

- **Why it matters:** Safety must not be bypassed by retrieval or provider behavior, but total outage handling affects availability.
- **Options:** pre-check only; post-check only; dual pre/post checks; fail-open on classifier outage; fail-closed or explicit error.
- **Current recommendation:** D-012 dual checks. Ambiguous decisions refuse; module crash returns `error` and never bypasses safety. Post-check ambiguity returns `refused_safety`.
- **Evidence needed:** Policy fixture coverage, latency, false refusal rate, operational failure tests.
- **Owner / stage:** Agent 08/09, integration stage.

## AQ-06 — Source prioritization and jurisdiction handling

- **Why it matters:** Authorities can disagree without one universal winner; population and jurisdiction make naive ranking unsafe.
- **Options:** authority-specific filters; metadata-aware ranking; single global priority list.
- **Current recommendation:** retain authority, jurisdiction, and population metadata; disclose requested-authority gaps; present conflicts separately; do not auto-pick a winner.
- **Evidence needed:** Curated source inventory and representative compare queries.
- **Owner / stage:** Agent 03/06/07, corpus and retrieval stages.

## AQ-07 — Data retention and privacy

- **Why it matters:** Query text may contain health information even without accounts. Persistence aids audit but increases exposure.
- **Options:** full short-term retention; redacted query persistence; configurable TTL with durable aggregate metrics.
- **Current recommendation:** MVP may persist query trace for demo/evaluation, minimize duplicated sensitive text, never store secrets, and document deletion/retention configuration before shared deployment.
- **Evidence needed:** Hosting environment, audit needs, privacy review, retention cost.
- **Owner / stage:** Agent 00/04/10, before production-like release.

## AQ-08 — LLM provider failure and fallback

- **Why it matters:** A fallback can improve availability but can alter model behavior, cost, and reproducibility; fake grounded success is unacceptable.
- **Options:** no fallback; approved secondary provider; cached answer fallback.
- **Current recommendation:** no silent fallback in MVP; provider/embedding failure maps to sanitized `error`. Any fallback needs a new decision and model trace metadata.
- **Evidence needed:** outage frequency, cost budget, compatibility tests, safety regression results.
- **Owner / stage:** Agent 07/09/10, post-MVP unless required.

## AQ-09 — Operational cost constraints

- **Why it matters:** Embedding and generation calls can make demos expensive, especially with retries and evaluation.
- **Options:** request budgets; model/config limits; caching; offline fixtures/mock provider.
- **Current recommendation:** record model IDs, tokens, latency, and estimated cost; use mock/no-op Langfuse mode when credentials are absent; calibrate limits from evaluation and demo load.
- **Evidence needed:** representative query distribution, provider pricing, local concurrency target.
- **Owner / stage:** Agent 10 with Agent 00, before external demo use.

## Related provisional decisions

- D-010: chunking strategy requires corpus evaluation.
- D-011: embedding/chat model defaults require quality and cost evaluation.
- D-015: insufficient-evidence gating requires calibration.
- D-019: sync DB access is the MVP default unless measured load justifies change.

## Resolution protocol

When an open question is resolved, add a new decision with the next available `D-XXX` identifier, update affected interface documents in the same change, and record the dependent agents/stages. Do not silently convert a recommendation into an approved requirement.
