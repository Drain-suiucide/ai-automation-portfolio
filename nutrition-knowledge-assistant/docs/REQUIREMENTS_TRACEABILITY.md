# Requirements Traceability — Nutrition Knowledge Assistant

**Status:** Active (Stage 3 architecture)
**Owner:** Agent 02
**Last updated:** 2026-11-18

This matrix maps every functional requirement (FR) and every acceptance criterion (AC) to the architecture that owns it. It is a design trace, not evidence that the requirement has been implemented or passed.

## Functional requirements

| ID | Architectural component | Interface / contract | Data entities | E2E scenario(s) | Evaluation / verification | Stage |
|---|---|---|---|---|---|---|
| FR-001 | API/Application, Query Validation | QUERY_INTERFACE | Query | S01, S04 | API validation + E2E ask | 10 |
| FR-002 | Safety Pre-check, orchestrator | SAFETY_INTERFACE | SafetyDecision, Query | S06-S08, S12 | Safety policy fixtures | 9 |
| FR-003 | Retrieval | RETRIEVAL_INTERFACE | Embedding, Chunk, RetrievalResult | S01-S05 | Recall@k / retrieval tests | 7 |
| FR-004 | Context Assembly, LLM Generation | GENERATION_INTERFACE | Evidence, GeneratedClaim | S01-S05 | Groundedness evaluation | 8 |
| FR-005 | Claim extraction, Citation Validation | GENERATION_INTERFACE, EVIDENCE_INTERFACE | GeneratedClaim, Citation | S01-S03, S05 | Claim-to-citation coverage | 8/11 |
| FR-006 | Citation Validation | GENERATION_INTERFACE | Chunk, DocumentVersion, Citation | S01, S10 | Deterministic validity gate | 8 |
| FR-007 | Evidence Filtering, Response Assembly | EVIDENCE_INTERFACE, QUERY_INTERFACE | Evidence, Query | S04 | Outcome accuracy | 7/8 |
| FR-008 | Safety Pre/Post-check | SAFETY_INTERFACE | SafetyDecision, Query | S06-S08, S12 | Refusal correctness | 9 |
| FR-009 | Context allow-list, Citation Validation | GENERATION_INTERFACE | Citation, Chunk | S01-S11 | Invalid-ID and hallucination tests | 8 |
| FR-010 | Context Assembly, Generation | GENERATION_INTERFACE | Evidence, GeneratedClaim | S01-S05 | Groundedness / forbidden parametric claims | 8/11 |
| FR-011 | Response Assembly, citation API | QUERY_INTERFACE, EVIDENCE_INTERFACE | Citation, DocumentVersion | S01-S03, S09 | API/UI contract checks | 10 |
| FR-012 | Chunk inspection endpoint | QUERY_INTERFACE | Chunk, DocumentVersion, Source | S01-S03, S09 | 404 and latency tests | 10 |
| FR-013 | Context Assembly trust boundary | GENERATION_INTERFACE | Chunk, Evidence | S07, S11 | Poisoned-chunk tests | 8/9 |
| FR-014 | Conflict Detection, Response Assembly | EVIDENCE_INTERFACE, QUERY_INTERFACE | Evidence, GeneratedClaim, Citation | S03, S05 | Conflict disclosure rate | 7/8/10 |
| FR-015 | Query Understanding, Coverage response | QUERY_INTERFACE, EVIDENCE_INTERFACE | DocumentVersion, Evidence, Query | S03 | Missing-authority scenario | 7/10 |
| FR-016 | Source Registry, Document Versioning | INGESTION_INTERFACE | Source, Document, DocumentVersion | S09 | Version metadata checks | 5/6 |
| FR-017 | Ingestion pipeline | INGESTION_INTERFACE | IngestionJob, DocumentVersion | S09 | AC-44 ingestion E2E | 6 |
| FR-018 | Chunking / persistence | INGESTION_INTERFACE | Chunk, DocumentVersion | S01-S04, S09 | FK and persistence tests | 5/6 |
| FR-019 | Embeddings / Vector Storage | RETRIEVAL_INTERFACE, INGESTION_INTERFACE | Embedding, Chunk | S01-S05 | pgvector integration test | 5/7 |
| FR-020 | Response Assembly, API | QUERY_INTERFACE | Query | S01-S12 | Status enum contract tests | 10 |
| FR-021 | Response Assembly, Frontend | QUERY_INTERFACE | Query | S01-S13 | Disclaimer assertions | 9/10 |
| FR-022 | API error handling, Observability | QUERY_INTERFACE | AuditEvent | S07, S10 | Secret/stack redaction tests | 9/10 |
| FR-023 | Provider adapters, orchestrator | RETRIEVAL_INTERFACE, GENERATION_INTERFACE | Query, AuditEvent | S10 | Forced provider failure | 7/8/10 |
| FR-024 | Frontend answer view | QUERY_INTERFACE | Query, Citation | S01-S12 | UI E2E | 10 |
| FR-025 | Frontend citation inspection | QUERY_INTERFACE, GET /chunks | Chunk, Citation | S01-S03, S09 | UI/API inspection test | 10 |
| FR-026 | Evidence Filtering, version metadata | EVIDENCE_INTERFACE | DocumentVersion, Citation | S09 | Outdated disclosure check | 7/10 |
| FR-027 | Feedback endpoint | QUERY_INTERFACE | FeedbackEvent, Query | — | Feedback contract test | 10 |
| FR-028 | Operator document listing | INGESTION_INTERFACE | Source, Document, DocumentVersion | — | Operator API test | 10 |
| FR-029 | Retrieval score labeling | RETRIEVAL_INTERFACE, QUERY_INTERFACE | RetrievalResult | S01-S03 | Schema/UI wording review | 7/10 |
| FR-030 | Observability / Langfuse adapter | operational span contract | Query, AuditEvent | S01, S10 | Trace/token/cost assertions | 10/11 |
| FR-031 | Document version deactivation | INGESTION_INTERFACE | DocumentVersion, Chunk | S09 | Retrieval exclusion test | 6 |
| FR-032 | Bad-citation feedback extension | QUERY_INTERFACE (later extension) | FeedbackEvent, Citation | — | Structured feedback test | Later |
| FR-033 | Safety Policy categories | SAFETY_INTERFACE | SafetyDecision | S06-S08, S12-S13 | AC-20–30 fixture suite | 9 |
| FR-034 | Allow-list for safe education | SAFETY_INTERFACE, QUERY_INTERFACE | SafetyDecision, Query | S01-S05, S13 | Safety allow recall | 9/10 |
| FR-035 | Product boundary / deployment | API and deployment architecture | — | — | Scope and threat review | 3/12 |

## Acceptance criteria

| ID | Owning architectural area | Verification artifact |
|---|---|---|
| AC-01 | API, Generation, Response Assembly | S01 E2E: `answered` + disclaimer |
| AC-02 | Claim/Citation Validation | Citation coverage test |
| AC-03 | Chunk inspection API/UI | Citation inspection E2E |
| AC-04 | Versioned provenance model | Citation metadata contract |
| AC-05 | Citation Validation | DB resolution test |
| AC-06 | Citation Validation | Invalid-ID rejection test |
| AC-07 | Generation + evaluation | Groundedness rubric |
| AC-08 | Evidence Filtering | S04 outcome test |
| AC-09 | Response status model | Status contract + UI test |
| AC-10 | Conflict Detection | S03/S05 conflict E2E |
| AC-11 | Coverage reporting | Missing-authority test |
| AC-12 | Score labeling | API/UI wording review |
| AC-20 | Safety Pre/Post | Diagnosis refusal fixture |
| AC-21 | Safety Pre/Post | Medication fixture |
| AC-22 | Safety Pre/Post | Extreme-weight-loss fixture |
| AC-23 | Safety Pre/Post | Eating-disorder fixture |
| AC-24 | Safety Pre/Post | Personalized-plan fixture |
| AC-25 | Safety classifier allow path | General nutrition allow fixture |
| AC-26 | Safety + heightened disclaimer | Pregnancy/children pair fixtures |
| AC-27 | Safety | Supplement dosing vs education fixtures |
| AC-28 | Safety emergency handling | Emergency redirect fixture |
| AC-29 | Safety + API sanitization | User injection red-team fixture |
| AC-30 | Context Assembly | Poisoned document fixture |
| AC-40 | Error handling + logging | Secret scanning/redaction tests |
| AC-41 | Provider adapters | Forced LLM failure E2E |
| AC-42 | Query/API validation | 4xx sanitized response test |
| AC-43 | Document versioning | Outdated-source scenario |
| AC-44 | Ingestion pipeline | Approved document ingest E2E |
| AC-45 | Feedback endpoint | Query-linked feedback test |
| AC-50 | Deployment architecture | Compose smoke test (Stage 12) |
| AC-51 | Frontend integration | Ask → answer → citation E2E |
| AC-52 | Observability | Langfuse/mock trace test |
| AC-53 | Evaluation runner | Baseline evaluation command/report |

## Traceability notes

- `answered_with_conflicts` is treated as a first-class terminal status per D-013.
- Citation validity is a runtime hard gate; citation support and groundedness are evaluation metrics in the MVP per D-016.
- A mapped stage is an ownership/dependency indication, not a claim that the stage is complete.
- FR-032 is intentionally later than the MVP core because the PRD marks it Could; the data model keeps an extensible `FeedbackEvent`.
