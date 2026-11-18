# Agent 02 Handoff — Solution Architecture & Technical Design

**Date:** 2026-11-18
**Status:** Stage 3 architecture documentation complete; application is not implemented.

## Implementation Summary

Published the implementation-ready architecture for Nutrition Knowledge Assistant as a modular monolith. The design preserves the approved product outcomes (`answered`, `answered_with_conflicts`, `insufficient_evidence`, `refused_safety`, `error`), establishes the evidence provenance chain, defines safety and citation gates, and publishes shared module contracts for downstream agents.

The repository already contained the main architecture, conceptual data model, seven interface contracts, and architecture decisions D-008–D-019 when this work began. This handoff records the completed Stage 3 set without overwriting those documents.

## Files Created

- `docs/REQUIREMENTS_TRACEABILITY.md`
- `docs/ARCHITECTURE_OPEN_QUESTIONS.md`
- `docs/handoffs/AGENT_02_HANDOFF.md`

## Files Modified

- None by this completion pass. Existing Stage 3 files were inspected and retained:
  - `docs/ARCHITECTURE.md`
  - `docs/DATA_MODEL.md`
  - `docs/interfaces/QUERY_INTERFACE.md`
  - `docs/interfaces/RETRIEVAL_INTERFACE.md`
  - `docs/interfaces/EVIDENCE_INTERFACE.md`
  - `docs/interfaces/GENERATION_INTERFACE.md`
  - `docs/interfaces/SAFETY_INTERFACE.md`
  - `docs/interfaces/INGESTION_INTERFACE.md`
  - `docs/interfaces/EVALUATION_INTERFACE.md`
- `docs/DECISIONS.md` already contains D-008–D-019 in the working tree; this handoff does not alter or reinterpret them.

## Main Architectural Decisions

1. **Modular monolith:** one FastAPI backend with explicit in-process modules; React/Vite remains a separate client.
2. **Transparent RAG pipeline:** validation → safety pre-check → query understanding → retrieval → evidence filtering/conflict detection → context assembly → generation → citation validity gate → safety post-check → response assembly.
3. **Dual safety enforcement:** safety runs before retrieval and after generation; ambiguity fails closed, and a safety module failure never bypasses the gate.
4. **First-class conflict outcome:** conflicting recommendations produce `answered_with_conflicts` and structured per-side citations.
5. **Citation validity hard gate:** cited chunk and document-version IDs must exist, match ownership, and belong to the request evidence set. Semantic citation support is evaluation-only in the MVP.
6. **Versioned provenance:** source, document, immutable document version, chunk, embedding, retrieval result, evidence, claim, and citation are traceable.
7. **No arbitrary score threshold yet:** empty/filtered evidence and failed citation validation produce `insufficient_evidence`; numerical relevance thresholds remain configurable and provisional until calibrated.
8. **Operator boundary:** shared bearer token for operator routes in the local MVP; no public exposure is implied.
9. **Explicit provider failures:** OpenAI/DB failures return sanitized `error`; no silent or untraced fallback.

## Component Boundaries

- **API/Application:** HTTP validation, auth for operator paths, response mapping, error sanitization.
- **Query/Safety:** input validation, policy classification, heightened disclaimers, refusal decisions.
- **Retrieval/Evidence:** embedding, pgvector search, metadata filtering, outdated disclosure, coverage and conflict representation.
- **Generation/Citations:** untrusted evidence context, structured claims, citation allow-list and database validation.
- **Ingestion/Sources:** approved source registry, license checks, fetch/extract/normalize/version/chunk/embed/store, idempotency and deactivation.
- **Evaluation/Observability:** deterministic integrity checks, labeled retrieval and scenario evaluation, Langfuse-compatible traces, token/cost/latency metrics.

All are backend modules, not separate services. There is no queue, microservice, or orchestration platform in the MVP design.

## Interface Contracts

The downstream implementation agents must consume the contracts under `docs/interfaces/`:

- Query and public HTTP response: `QUERY_INTERFACE.md`
- Retrieval candidates: `RETRIEVAL_INTERFACE.md`
- Evidence, conflicts, coverage, and shared citation shape: `EVIDENCE_INTERFACE.md`
- Context, generation draft, and citation validity gate: `GENERATION_INTERFACE.md`
- Pre/post safety decisions: `SAFETY_INTERFACE.md`
- Source registration and ingestion lifecycle: `INGESTION_INTERFACE.md`
- Evaluation datasets, runs, and metrics: `EVALUATION_INTERFACE.md`

The frontend consumes only the query and chunk-inspection contracts; it does not access the database or OpenAI directly.

## Data Model Summary

`DATA_MODEL.md` defines persistent conceptual entities: Source, Document, DocumentVersion, Chunk, Embedding, IngestionJob, Query, RetrievalResult, Evidence, GeneratedClaim, Citation, EvaluationRun, EvaluationResult, SafetyDecision, AuditEvent, and FeedbackEvent. Key invariants are:

- every chunk belongs to exactly one document version;
- citation version must own the cited chunk;
- only approved and active versions enter default retrieval;
- outdated versions remain auditable and are disclosed when cited;
- successful grounded responses cannot contain unresolved citations;
- secrets never enter persisted entities or audit payloads.

## Requirements Traceability Status

`docs/REQUIREMENTS_TRACEABILITY.md` maps all FR-001 through FR-035 and all listed AC-01–AC-53 to owning components, interfaces/entities, scenarios, evaluation methods, and implementation stages. It explicitly labels mapping as design traceability rather than implementation completion.

## Unresolved Questions

`docs/ARCHITECTURE_OPEN_QUESTIONS.md` records licensing/rights for WHO and USDA content, operator auth beyond local MVP, evidence sufficiency calibration, runtime citation-support verification, safety failure policy, jurisdiction/source prioritization, retention/privacy, provider fallback, and cost constraints. These are not silently decided.

## Known Limitations

- No backend, frontend, database migration, ingestion runner, retrieval implementation, safety classifier, or evaluation runner exists yet.
- Exact embedding/chat model IDs and vector dimensions remain provisional under D-011.
- Chunking parameters remain provisional under D-010.
- Citation support/groundedness is not a runtime semantic guarantee in the MVP.
- The real source corpus and licensing status are not supplied; Agent 03 must clear sources or use clearly labeled fixtures.
- Rate limiting is described as a deployment concern but requires calibration before exposure beyond a local demo.
- Documentation-only work has no application test suite to execute.

## Validation Performed

- Confirmed all mandatory upstream requirements, safety, acceptance, risk, scenario, decision, and handoff documents exist and were read.
- Confirmed the required architecture files and all seven interface contracts exist.
- Confirmed the five normative response outcomes appear in the architecture, query contract, data model, and evaluation contract.
- Confirmed citation validity and citation support are described as separate concepts.
- Confirmed document-version and chunk ownership invariants are consistent across architecture, data model, and interfaces.
- Confirmed safety coverage includes supplements, medication interactions, eating disorders, extreme weight loss, pregnancy, children, emergencies, prompt injection, and insufficient evidence.
- Confirmed no application code, migrations, infrastructure, or package installation was introduced.
- `git diff --check` is required after the documentation commit; no runtime tests are applicable to this documentation-only stage.

## Recommended Implementation Sequence

1. **Agent 03 — Knowledge Sources:** resolve licensing/provenance, define source catalog, and provide labeled fixtures for WHO/USDA comparison, conflicts, outdated content, and poisoned chunks.
2. **Agent 04 — Database & Infrastructure:** implement SQLAlchemy/Alembic schema and Compose PostgreSQL/pgvector using `DATA_MODEL.md`; document secrets and health checks.
3. **Agent 05 — Ingestion:** implement the transactional, idempotent pipeline against `INGESTION_INTERFACE.md`.
4. **Agent 06 — Retrieval:** implement query embedding, active-version filtering, top-k retrieval, evidence selection, and calibrated evaluation hooks.
5. **Agent 07 — Generation & Citations:** implement context isolation, structured generation, citation validation, retry/abstention behavior.
6. **Agent 08 — Safety:** implement rules-first pre/post checks and policy fixture tests; integrate without changing shared contracts.
7. **Agent 09 — API & Frontend:** expose `/api/v1` and build the ask → status → citation inspection flow from the published contracts.
8. **Agent 10 — Evaluation & Observability:** add scenario datasets, deterministic integrity metrics, support/groundedness evaluation, and Langfuse/mock tracing.
9. **Agent 11 — Independent Audit:** verify safety, citation, contract, and DoD claims after Stages 1–12.

## Dependencies Between Future Agents

- Agent 03 and Agent 04 can proceed in parallel after consuming the contracts.
- Agent 05 requires Agent 03 source metadata and Agent 04 persistence.
- Agent 06 requires Agent 05 searchable chunks and Agent 04 vector storage.
- Agent 07 requires Agent 06 retrieval/evidence shapes.
- Agent 08 can implement policy logic in parallel, but integration must happen before API completion.
- Agent 09 must consume, not redefine, the query/retrieval/generation/safety contracts.
- Agent 10 depends on observable outputs from Agents 05–09 and must report regressions rather than alter production behavior.

## Exact Next Agent Recommendation

**Start Agent 03 (Knowledge Sources) and Agent 04 (Database & Infrastructure) in parallel.** Both are unblocked by this documentation set; Agent 03 should resolve the licensing open question and fixtures, while Agent 04 should implement persistence strictly from the conceptual model and interface contracts.

### Implementation Summary
Architecture documentation and shared contracts are complete; no application runtime was implemented.

### Files Created
- `docs/REQUIREMENTS_TRACEABILITY.md`
- `docs/ARCHITECTURE_OPEN_QUESTIONS.md`
- `docs/handoffs/AGENT_02_HANDOFF.md`

### Files Modified
- None in the completion pass.

### Technical Decisions
See D-008–D-019 and `docs/ARCHITECTURE.md`; key choices are modular monolith, transparent RAG, dual safety checks, first-class conflicts, and citation validity hard gate.

### Tests
N/A — documentation only. Validation consists of document existence/consistency checks and `git diff --check`.

### Known Limitations
No runtime components are implemented; provisional thresholds/models/chunking and open questions remain explicit.

### Integration Contract
Downstream agents implement against the seven interface documents and preserve the data-model invariants and exact status vocabulary.

### Next Agent Handoff
Start Agents 03 and 04 in parallel; do not start Agent 05 until source and persistence contracts are available.
