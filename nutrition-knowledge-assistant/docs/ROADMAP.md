# Development Roadmap

**Status:** Active  
**Owner:** Agent 00  
**Last updated:** 2026-11-18

Stages are sequential unless dependencies explicitly allow parallelism (see `docs/AGENT_WORKFLOW.md`).

---

## Stage 1 — Project Setup

**Owner:** Agent 00  
**Goal:** Establish a governed, empty-but-ready repository foundation.

**Tasks:**
- Initialize project directory structure.
- Add README, AGENTS.md, .gitignore.
- Publish charter, workflow, roadmap, decision log.

**Deliverables:**
- `README.md`, `AGENTS.md`, `.gitignore`
- `docs/PROJECT_CHARTER.md`, `docs/AGENT_WORKFLOW.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`
- Placeholder dirs: `docs/`, `evaluation/`, `data/`, `tests/`

**Dependencies:** None.

**Acceptance criteria:**
- Another agent can start without asking what the product is.
- No fictitious runtime implementation.
- Git available at portfolio root; project path documented.

---

## Stage 2 — Product Requirements

**Owner:** Agent 01  
**Goal:** Define what to build and what must never be built.

**Tasks:**
- Write PRD with personas, stories, non-functional requirements.
- Define Safety Policy outline (medical boundaries, vulnerable users).
- Specify MVP acceptance scenarios and edge cases.
- Clarify citation UX and `insufficient_evidence` behavior.

**Deliverables:**
- Product requirements document
- Safety policy (outline or full, as scoped)
- Acceptance checklist for MVP

**Dependencies:** Stage 1.

**Acceptance criteria:**
- Scope and out-of-scope are unambiguous.
- Safety boundaries are testable.
- Requirements are sufficient for architecture without inventing product intent.

---

## Stage 3 — Architecture

**Owner:** Agent 02  
**Goal:** Publish system design and shared contracts.

**Tasks:**
- Module boundaries (API, ingest, retrieve, generate, cite, safety, eval, observability).
- Data model proposal (documents, versions, chunks, embeddings, queries, citations).
- Interface contracts between modules.
- Deployment topology for local Docker Compose.
- Threat/trust model for retrieved content.

**Deliverables:**
- Architecture document
- Interface specs under `docs/interfaces/` (or equivalent)
- Decisions appended to `docs/DECISIONS.md` for architecture choices

**Dependencies:** Stage 2.

**Acceptance criteria:**
- Downstream agents have clear ownership and contracts.
- No duplicate service interfaces.
- Stack matches approved decisions unless RFC approved.

---

## Stage 4 — Knowledge Sources

**Owner:** Agent 03  
**Goal:** Define and prepare a curated, rights-cleared knowledge base inventory.

**Tasks:**
- Catalog official/scientific sources.
- Document license, provenance, versioning, and update policy.
- Define document metadata schema (aligned with Architecture).
- Provide acquisition/normalization notes for ingestion.

**Deliverables:**
- Source catalog
- Metadata standard
- Sample source set or acquisition instructions under `data/` / `docs/sources/`

**Dependencies:** Stage 3.

**Acceptance criteria:**
- Every source has provenance and license status.
- Ingestion can proceed without guessing metadata fields.

---

## Stage 5 — Database & Infrastructure

**Owner:** Agent 04  
**Goal:** Provide persistent storage and local runnable infrastructure.

**Tasks:**
- PostgreSQL + pgvector schema via SQLAlchemy/Alembic.
- Docker Compose for app dependencies.
- Environment variable documentation (`.env.example`).
- Health checks and basic connectivity verification.

**Deliverables:**
- Migrations
- Compose stack
- Infra docs

**Dependencies:** Stage 3.

**Acceptance criteria:**
- Fresh environment can migrate and connect.
- Vector storage is available for embeddings.
- Secrets are not hardcoded.

---

## Stage 6 — Ingestion

**Owner:** Agent 05  
**Goal:** Turn approved documents into versioned chunks with embeddings.

**Tasks:**
- Parse and normalize documents.
- Chunk into meaningful units.
- Generate embeddings (OpenAI API per approved stack).
- Persist documents, chunks, vectors.
- Idempotent re-ingestion / version handling per architecture.

**Deliverables:**
- Ingestion pipeline module(s)
- Tests for parse/chunk/store paths
- Operator documentation

**Dependencies:** Stages 4 and 5.

**Acceptance criteria:**
- A sample document can be ingested end-to-end.
- Chunks are addressable and version-linked.
- Failures surface with structured errors/logs.

---

## Stage 7 — Retrieval

**Owner:** Agent 06  
**Goal:** Return relevant evidence for a user query.

**Tasks:**
- Query embedding.
- Similarity search over pgvector.
- Ranking / top-k selection per architecture.
- Retrieval service contract implementation.

**Deliverables:**
- Retrieval module
- Unit/integration tests
- Retrieval quality hooks for Stage 11/10

**Dependencies:** Stage 6.

**Acceptance criteria:**
- Retrieval returns chunk IDs, scores, and metadata needed for citation.
- Similarity scores are not labeled as factual probabilities.
- Empty/low-evidence cases are representable.

---

## Stage 8 — Generation & Citations

**Owner:** Agent 07  
**Goal:** Produce grounded answers with validated citations.

**Tasks:**
- Prompt design constrained to retrieved evidence.
- Answer generation via OpenAI API.
- Attach citations to significant factual claims.
- Validate citations against existing chunks/document versions.
- Support `insufficient_evidence` outcomes.
- Prevent presentation of parametric knowledge as KB-verified.

**Deliverables:**
- Generation + citation modules
- Tests for citation validation and refusal-of-unsupported-claims
- Prompt/docs contracts

**Dependencies:** Stage 7.

**Acceptance criteria:**
- Unsupported claims are not emitted as verified.
- Invalid citations are rejected.
- Grounded answers include resolvable citations.

---

## Stage 9 — Safety

**Owner:** Agent 08  
**Goal:** Enforce Safety Policy on user intents and generated outputs.

**Tasks:**
- Implement policy checks (diagnosis, treatment, meds, dangerous weight-loss, etc.).
- Integrate with API answer path.
- Define refusal / safe-redirect responses.
- Add tests for policy scenarios.

**Deliverables:**
- Safety module
- Policy-aligned test suite
- Integration notes for API/generation

**Dependencies:** Stages 2 and 3; integration before Stage 10 (API) completion. May develop in parallel with 5–7.

**Acceptance criteria:**
- Policy-defined unsafe requests are refused.
- Safety is not bypassable by prompt injection from retrieved text.
- Demo incentives do not weaken controls.

---

## Stage 10 — API & Frontend

**Owner:** Agent 09  
**Goal:** Deliver a working web application for the ask → answer → cite flow.

**Tasks:**
- FastAPI endpoints per architecture contracts.
- React + TypeScript + Vite UI.
- Display answers, citations, insufficient evidence, and safety refusals.
- Wire observability hooks as specified by Stage 11/10 contracts.

**Deliverables:**
- API service
- Frontend app
- API docs (OpenAPI)
- Basic E2E happy-path verification

**Dependencies:** Stages 4–9 (core services available).

**Acceptance criteria:**
- User can ask a question in the UI and see a cited or refused response.
- Errors are user-visible and logged structurally.
- No secrets in frontend bundles.

---

## Stage 11 — Evaluation

**Owner:** Agent 10  
**Goal:** Measure retrieval quality, answer quality, and operational metrics.

**Tasks:**
- Build evaluation datasets and runners under `evaluation/`.
- Measure retrieval and answer quality.
- Instrument Langfuse for latency, tokens, cost.
- Publish how to interpret scores (incl. similarity ≠ factual probability).

**Deliverables:**
- Eval suite + docs
- Sample reports under `evaluation/results/` (generated, gitignored content)
- Observability integration

**Dependencies:** Stages 6–10.

**Acceptance criteria:**
- Eval commands are documented and runnable.
- Metrics cover grounding/citation/safety-relevant cases where applicable.
- Cost/latency/token tracking is visible in Langfuse (or documented mock mode).

---

## Stage 12 — Deployment

**Owner:** Agent 04 (infra) + Agent 09 (app) coordination; Tech Lead oversight  
**Goal:** Make local (and documented) deployment reproducible.

**Tasks:**
- Finalize Docker Compose production-like local profile.
- Document runbooks: env vars, migrate, ingest sample, start UI.
- Smoke test full path.

**Deliverables:**
- Deployment docs
- Compose profiles / scripts as needed

**Dependencies:** Stages 5 and 10; preferably after Stage 11 baseline.

**Acceptance criteria:**
- Clean machine instructions work with documented prerequisites.
- Smoke test covers ask → retrieve → answer → cite.

---

## Stage 13 — Independent Audit

**Owner:** Agent 11  
**Goal:** Independently verify grounding, safety, contracts, and DoD honesty.

**Tasks:**
- Review citations, safety refusals, and hallucinated-source risks.
- Verify agents did not invent passing tests.
- Check shared contract consistency.
- File findings and severity.

**Deliverables:**
- Audit report under `docs/audit/`
- Prioritized remediation list

**Dependencies:** Stages 1–12 (as complete).

**Acceptance criteria:**
- Findings are actionable and evidence-based.
- Critical grounding/safety issues are explicitly called out.
- No silent scope reduction of safety or citation rules.

---

## Progress Snapshot

| Stage | Status |
|-------|--------|
| 1 Project Setup | Complete (Agent 00) |
| 2 Product Requirements | Complete (Agent 01) |
| 3–13 | Not started |
