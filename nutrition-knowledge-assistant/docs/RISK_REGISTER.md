# Risk Register — Nutrition Knowledge Assistant

**Status:** Active (Stage 2)
**Owner:** Agent 01
**Last updated:** 2026-11-18
**Related:** `docs/SAFETY_POLICY.md`, threat model in §2, `docs/PRD.md`

Likelihood / Impact: **L** Low · **M** Medium · **H** High · **C** Critical (impact)

---

## 1. Product risks

| ID | Risk | Likeli. | Impact | Mitigation | Owner |
|----|------|---------|--------|------------|-------|
| PR-01 | Users treat outputs as personal medical advice | H | H | Hard disclaimer; Safety Policy refusals; UI framing | 01/08/09 |
| PR-02 | Over-refusal makes demo look broken / useless | M | M | FR-034; category tests requiring allow-list educational answers | 01/08/10 |
| PR-03 | Under-scoped KB → frequent `insufficient_evidence` | H | M | Curate solid MVP corpus (Agent 03); disclose coverage | 03/05 |
| PR-04 | Scope creep into clinical decision support | M | H | MoSCoW Won't Have; Decision RFC required to expand | 00/01 |
| PR-05 | Ambiguous UX between error / refuse / insufficient | M | M | Distinct statuses; acceptance AC-09 | 02/09 |

---

## 2. Scientific / content risks

| ID | Risk | Likeli. | Impact | Mitigation | Owner |
|----|------|---------|--------|------------|-------|
| SR-01 | Outdated guidelines presented as current | M | H | Versioning + outdated flag + disclosure (FR-026) | 03/05/07 |
| SR-02 | Conflicting authorities silently merged | M | H | Conflict presentation requirement; AC-10 | 07/09 |
| SR-03 | Weak citation support (valid id, wrong entailment) | H | H | Hard citation validity gate; eval for support; iterative NLI/heuristics | 07/10 |
| SR-04 | Licensing / provenance gaps in sources | M | H | Source catalog with license status before ingest | 03 |
| SR-05 | Similarity mistaken for truth by users/devs | M | M | Labeling rules; docs; eval narrative | 01/09/10 |

---

## 3. Safety risks

| ID | Risk | Likeli. | Impact | Mitigation | Owner |
|----|------|---------|--------|------------|-------|
| SF-01 | Unsafe medical advice escapes filters | M | C | Dual input/output checks; category tests; audit | 08/11 |
| SF-02 | ED / extreme loss coaching leakage | M | C | L3 refusals; red-team cases in eval | 08/10 |
| SF-03 | Pediatric/pregnancy personalization leakage | M | H | Cat 10–11 rules; heightened disclaimer | 08 |
| SF-04 | Medication interaction advice leakage | M | C | Cat 7 hard refuse | 08 |
| SF-05 | Safety weakened for demo polish | L | H | Explicit policy change control; Agent 11 audit | 00/11 |

---

## 4. Technical risks

| ID | Risk | Likeli. | Impact | Mitigation | Owner |
|----|------|---------|--------|------------|-------|
| TR-01 | Hallucinated citations | H | H | Validate citations against DB before return | 07 |
| TR-02 | Prompt injection via user or documents | H | H | Untrusted retrieval; instruction hierarchy; tests | 08/07 |
| TR-03 | Document poisoning in curated KB | M | H | Human-approved source list; no open crawl in MVP | 03/05 |
| TR-04 | OpenAI API outage / rate limits | M | M | Explicit `error` path; retries per Architecture | 07/09 |
| TR-05 | Cost overruns on embeddings/generation | M | M | Langfuse cost tracking; eval budgets | 10 |
| TR-06 | pgvector / schema drift across agents | M | H | Shared contracts + Alembic; RFC process | 02/04 |
| TR-07 | Secret leakage in logs/UI | L | H | Sanitization; AC-40; review | 09/04 |
| TR-08 | Non-reproducible answers (model drift) | M | M | Record model ids; pin versions where practical | 02/10 |

---

## 5. Threat model

| ID | Threat | Likelihood | Impact | Mitigation | Verification |
|----|--------|------------|--------|------------|--------------|
| TM-01 | **Prompt injection** (user) | H | H | System/safety instructions take precedence; ignore “disable safety” | Red-team tests AC-29 |
| TM-02 | **Document poisoning** (malicious/incorrect curated doc) | M | H | Manual source approval; provenance; deactivate versions | Source review checklist; soft-deactivate Could Have |
| TM-03 | **Malicious documents** with embedded instructions | M | H | Treat chunks as data; strip/ignore instruction patterns in context building | Automated injection-in-chunk tests AC-30 |
| TM-04 | **Hallucinated citations** | H | H | Pre-response citation validity gate | Unit/integration tests AC-05/06 |
| TM-05 | **Outdated recommendations** | M | H | Version + outdated tracking; disclose | AC-43; curator process |
| TM-06 | **Conflicting guidelines** mis-handled | M | H | Separate presentation; conflict status/section | Scenario S05; AC-10 |
| TM-07 | **Data leakage** (secrets, PII in logs) | L | H | Env secrets; sanitize errors; minimize PII retention (MVP: avoid storing unnecessary personal health data) | AC-40; log review |
| TM-08 | **API abuse** (cost/DoS on LLM endpoints) | M | M | Local demo assumption; rate limiting decision deferred to Architecture if exposed | Load smoke; optional rate limit Decision |
| TM-09 | **Unsafe medical advice** generation | M | C | Safety Policy categories + output filter | AC-20–28; audit |

---

## 6. Residual risk statement

Even with mitigations, the system **cannot guarantee** clinical correctness or completeness of the scientific literature. Residual risk of user over-trust remains **accepted** for an informational demo and must stay disclosed in UI and README.
