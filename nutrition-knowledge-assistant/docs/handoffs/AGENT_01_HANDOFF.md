# Agent 01 Handoff — Product Requirements & AI Safety

**Date:** 2026-11-18  
**Status:** Stage 2 complete (documentation only — no runtime code)

---

### Implementation Summary

Defined product requirements, MoSCoW MVP scope, evidence/trust vocabulary, Safety Policy (13 categories), acceptance criteria, risk/threat register, and 10+ end-to-end scenarios. Resolved Charter language TBD (English MVP). No API, DB, ingestion, RAG, or UI implementation.

### Files Created

- `docs/PRD.md`
- `docs/SAFETY_POLICY.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/RISK_REGISTER.md`
- `docs/USER_SCENARIOS.md`
- `docs/handoffs/AGENT_01_HANDOFF.md`

### Files Modified

- `README.md` — status + documentation map (consistency with Stage 2)
- `docs/ROADMAP.md` — progress snapshot Stage 1 complete / Stage 2 complete

### Technical Decisions (product-level; not architecture)

1. **English-only MVP** language policy (Charter TBD closed).
2. **Distinct outcomes:** `answered`, `answered_with_conflicts`, `insufficient_evidence`, `refused_safety`, `error`.
3. **Citation validity is a hard ship gate**; citation support measured in eval (may be heuristic in MVP).
4. **Do not over-refuse** educational Cat 1–3 questions.
5. **Threat model** recorded in `docs/RISK_REGISTER.md` §5.
6. **No new stack decisions** — D-001–D-007 unchanged; no Agent 02 architecture choices pre-empted.

### Tests

N/A — documentation only. No pytest execution.

### Known Limitations

- Safety **implementation** not built (Agent 08).
- Exact API/DB schemas not defined (Agent 02).
- Real WHO/USDA corpus licensing unresolved (Agent 03); scenarios allow labeled fixtures.
- AuthN for operator endpoints deferred.
- Automated citation-entailment depth deferred to Architecture + Eval.
- Stage 1 README previously said “Stage 1 current”; updated for consistency.

### Integration Contract

Downstream agents **must** treat these as normative product constraints:

| Document | Use for |
|----------|---------|
| `docs/PRD.md` | FRs/NFRs, personas, stories, MoSCoW, evidence definitions, status semantics |
| `docs/SAFETY_POLICY.md` | Category behaviors, refusal vs allow, testing requirements |
| `docs/ACCEPTANCE_CRITERIA.md` | Demo/MVP pass bar |
| `docs/USER_SCENARIOS.md` | E2E fixtures and expected processing |
| `docs/RISK_REGISTER.md` | Threat mitigations to design against |

Do **not** invent conflicting product statuses or weaken safety categories without Decision RFC.

### Consistency notes vs Agent 00

| Finding | Resolution |
|---------|------------|
| README/ROADMAP said Stage 1 in progress; handoff said complete | Progress markers updated |
| Workflow said Safety Policy “outline”; Stage 2 task asked full policy | Delivered full `SAFETY_POLICY.md` |
| Charter language TBD | Closed in PRD §7 |
| Agent count “11 agents” vs IDs 00–11 | Interpreted as Agent 00 plus 01–11 roster (12 named roles); left as Agent 00 wording — Architecture need not change |

### Next Agent Handoff — Agent 02 (Architecture)

**Unblocked.** Produce:

1. `docs/ARCHITECTURE.md` — module boundaries aligned to PRD FRs.
2. `docs/interfaces/*` — contracts for: ask API, retrieval result, citation object, safety decision, ingest, error model.
3. Data model: documents, versions, chunks, embeddings, queries, citations, outdated flags, optional feedback.
4. Pipeline order resolving open question: safety pre-retrieve / post-generate / both (recommend both per Safety Policy §5).
5. Threat/trust handling for retrieved content (TM-01–TM-03).
6. Append architecture Decisions to `docs/DECISIONS.md` (models, layout, auth stance for MVP).
7. Map each Must Have FR + AC-M to owning module.
8. `docs/handoffs/AGENT_02_HANDOFF.md`.

**Consume without rewriting product intent:** PRD, Safety Policy, Scenarios, Acceptance, Risks.

**Do not:** implement services; expand MVP into clinical CDS; choose to hide `insufficient_evidence`.

**Open questions for Agent 02 (must answer or defer explicitly):**

1. Safety enforcement placement and interfaces.
2. Operator endpoint AuthN for local Compose.
3. Threshold / policy for `insufficient_evidence` vs weak hits.
4. Whether conflicts are status enum vs flag.
5. Citation-support checker scope in MVP runtime vs eval-only.
6. Rate limiting if API exposed beyond localhost.
7. Exact embedding/generation model IDs.
