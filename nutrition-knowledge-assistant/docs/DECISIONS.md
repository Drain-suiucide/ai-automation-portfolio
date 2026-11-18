# Decision Log

**Status:** Active  
**Owner:** Agent 00 (bootstrap entries); later architecture decisions owned by Agent 02 via RFC  
**Last updated:** 2026-11-18 (Agent 02 architecture decisions appended)

Only **approved** or explicitly **provisional** decisions are listed. Do not treat drafts or agent assumptions as approved until recorded here.

---

## Decision index

| ID | Title | Status | Date |
|----|-------|--------|------|
| D-001 | Backend language & web framework | Approved | 2026-11-18 |
| D-002 | Primary datastore & vectors | Approved | 2026-11-18 |
| D-003 | LLM & embeddings provider | Approved | 2026-11-18 |
| D-004 | Frontend stack | Approved | 2026-11-18 |
| D-005 | Test runner | Approved | 2026-11-18 |
| D-006 | Observability | Approved | 2026-11-18 |
| D-007 | Containerization | Approved | 2026-11-18 |
| D-008 | Modular monolith package layout | Approved | 2026-11-18 |
| D-009 | Custom transparent RAG pipeline | Approved | 2026-11-18 |
| D-010 | Chunking strategy (MVP) | Provisional | 2026-11-18 |
| D-011 | Embedding & chat model defaults | Provisional | 2026-11-18 |
| D-012 | Dual safety enforcement (pre + post) | Approved | 2026-11-18 |
| D-013 | Conflict as distinct status | Approved | 2026-11-18 |
| D-014 | Operator auth via shared token | Approved | 2026-11-18 |
| D-015 | Insufficient-evidence gating | Provisional | 2026-11-18 |
| D-016 | Citation support eval-only in MVP | Approved | 2026-11-18 |
| D-017 | API versioning `/api/v1` | Approved | 2026-11-18 |
| D-018 | No hybrid search / reranker in MVP | Approved | 2026-11-18 |
| D-019 | Sync DB access default for MVP | Provisional | 2026-11-18 |

---

## D-001 — Backend language & web framework

- **Status:** Approved  
- **Decision:** Python 3.11+ with FastAPI and Pydantic.  
- **Rationale:** Strong typing ecosystem for APIs, async where useful, wide RAG/data tooling support.  
- **Consequences:** API and service code are Python-first; agents must use type hints and Pydantic validation at boundaries.  
- **Not decided here:** Package layout, DI style, sync vs async DB drivers (Agent 02).

---

## D-002 — Primary datastore & vectors

- **Status:** Approved  
- **Decision:** PostgreSQL with pgvector; SQLAlchemy + Alembic for ORM/migrations.  
- **Rationale:** Single operational store for relational metadata and embeddings; mature migration tooling.  
- **Consequences:** Infrastructure agent must provision Postgres + pgvector; vector schema is a shared contract.  
- **Not decided here:** Exact table schemas, index types, embedding dimensions (Agent 02 / 04).

---

## D-003 — LLM & embeddings provider

- **Status:** Approved  
- **Decision:** OpenAI API for embeddings and generation.  
- **Rationale:** Default stack requirement; reduces bootstrap complexity for MVP.  
- **Consequences:** Requires `OPENAI_API_KEY` (or equivalent) via environment; cost/latency must be tracked.  
- **Not decided here:** Specific models, temperature, chunk embedding strategy, fallbacks (Agent 02 / 05 / 07).

---

## D-004 — Frontend stack

- **Status:** Approved  
- **Decision:** React + TypeScript + Vite.  
- **Rationale:** Standard, lightweight SPA toolchain without unnecessary meta-frameworks.  
- **Consequences:** Frontend lives as a Vite app; consumes documented HTTP/OpenAPI contracts.  
- **Not decided here:** UI component library, routing, state management (Agent 09; keep minimal).

---

## D-005 — Test runner

- **Status:** Approved  
- **Decision:** pytest for Python tests; Ruff for linting.  
- **Rationale:** Default stack; simple and widely understood.  
- **Consequences:** Agents add pytest suites under `tests/`; CI (when added) should invoke pytest + ruff.  
- **Not decided here:** Frontend test runner (Agent 09 if needed).

---

## D-006 — Observability

- **Status:** Approved  
- **Decision:** Langfuse for tracing and operational metrics (latency, tokens, cost).  
- **Rationale:** Default stack for LLM observability.  
- **Consequences:** Instrumentation contracts must be documented; local/dev must support missing Langfuse credentials gracefully or via documented mock mode.  
- **Not decided here:** Exact span taxonomy and sampling (Agent 10 / 02).

---

## D-007 — Containerization

- **Status:** Approved  
- **Decision:** Docker + Docker Compose for local multi-service runtime.  
- **Rationale:** Reproducible Postgres/pgvector and app services.  
- **Consequences:** Infra docs must include Compose-based quickstart; no machine-specific paths in Compose files.  
- **Not decided here:** Cloud deployment target, K8s, managed Postgres (out of MVP unless later approved).

---

## Explicitly deferred to Agent 02 (Architecture)

Do **not** treat the following as decided until Agent 02 records them:

- Monorepo package layout (`backend/`, `frontend/`, etc.)
- Exact RAG orchestration style (custom pipeline vs light helpers)
- Chunking strategy and overlap
- Embedding model identity and vector dimensions
- Hybrid search / reranking
- AuthN/AuthZ for MVP
- API versioning scheme
- Citation JSON schema details
- Safety enforcement placement (pre-retrieval vs post-generation vs both) beyond high-level module separation

---

## How to add a decision

1. Assign next `D-XXX` ID.  
2. Include Status, Decision, Rationale, Consequences, Not decided / Alternatives.  
3. Link impacted agents.  
4. If breaking a shared contract, follow RFC rules in `docs/AGENT_WORKFLOW.md`.
