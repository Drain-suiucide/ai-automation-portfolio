# Nutrition Knowledge Assistant

RAG-based informational assistant for **general nutrition questions**, grounded in a curated knowledge base of official recommendations and scientific publications.

**Current status: Stage 3 (Architecture) documentation complete. Not a working product yet.**

This repository folder contains project governance and product/safety requirements. There is no runnable API, database, ingestion pipeline, or UI at this stage.

---

## Purpose

Help users get **verifiable** answers about nutrition topics by:

1. retrieving evidence from curated documents;
2. generating answers constrained to that evidence;
3. citing exact document fragments (chunk + document version);
4. returning `insufficient_evidence` when support is missing;
5. refusing unsafe medical / clinical requests per Safety Policy.

This is an **informational demonstration system**, not a medical diagnosis or treatment tool.

---

## Planned capabilities (MVP)

- Curated source ingestion (parse → chunk → embed → store)
- Semantic retrieval (PostgreSQL + pgvector)
- Grounded answer generation with citation validation
- Safety boundaries for medical and vulnerable-user scenarios
- Web UI for ask → answer → inspect citations
- Evaluation of retrieval/answer quality
- Observability for latency, tokens, and cost (Langfuse)

---

## Technology stack (approved)

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| API | FastAPI + Pydantic |
| ORM / migrations | SQLAlchemy + Alembic |
| Database | PostgreSQL + pgvector |
| LLM / embeddings | OpenAI API |
| Frontend | React + TypeScript + Vite |
| Tests / lint | pytest, Ruff |
| Observability | Langfuse |
| Runtime packaging | Docker + Docker Compose |

Details and deferred choices: [`docs/DECISIONS.md`](docs/DECISIONS.md).

---

## Repository layout (bootstrap)

```
nutrition-knowledge-assistant/
├── AGENTS.md                 # Rules for AI/human agents
├── README.md                 # This file
├── .gitignore
├── docs/                     # Charter, roadmap, governance, decisions
├── data/                     # Knowledge artifacts (raw/processed placeholders)
├── evaluation/               # Future eval suites & results
└── tests/                    # Future automated tests
```

Application packages (`backend/`, `frontend/`, etc.) will be introduced by Architecture (Agent 02) and implementing agents — **not invented here**.

---

## Documentation map

| Document | Description |
|----------|-------------|
| [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md) | Product purpose, scope, success criteria |
| [`docs/AGENT_WORKFLOW.md`](docs/AGENT_WORKFLOW.md) | Agent roles, dependencies, handoffs |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Staged delivery plan |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Approved technology decisions |
| [`docs/PRD.md`](docs/PRD.md) | Product requirements, stories, FRs/NFRs, MVP MoSCoW |
| [`docs/SAFETY_POLICY.md`](docs/SAFETY_POLICY.md) | Medical/AI safety categories and refusal rules |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, workflows, safety, data and deployment architecture |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Conceptual entities, relationships and retention |
| [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md) | FR/AC mapping to components, scenarios and verification |
| [`docs/ARCHITECTURE_OPEN_QUESTIONS.md`](docs/ARCHITECTURE_OPEN_QUESTIONS.md) | Unresolved architecture and operational questions |
| [`docs/interfaces/`](docs/interfaces/) | Shared module and API interface contracts |
| [`docs/ACCEPTANCE_CRITERIA.md`](docs/ACCEPTANCE_CRITERIA.md) | Verifiable MVP acceptance checks |
| [`docs/USER_SCENARIOS.md`](docs/USER_SCENARIOS.md) | End-to-end scenario specifications |
| [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) | Product/tech/safety risks and threat model |
| [`AGENTS.md`](AGENTS.md) | Engineering standards for agents |

---

## Roadmap (summary)

1. Project Setup ← complete
2. Product Requirements ← **current complete**
3. Architecture ← next
4. Knowledge Sources
5. Database & Infrastructure
6. Ingestion
7. Retrieval
8. Generation & Citations
9. Safety
10. API & Frontend
11. Evaluation
12. Deployment
13. Independent Audit

Full detail: [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Development rules (short)

- Implement only your assigned module; respect ownership in `docs/AGENT_WORKFLOW.md`.
- Do not invent shared API/DB contracts; follow Architecture docs or file an RFC in `docs/DECISIONS.md`.
- No secrets in git; configure via environment variables.
- Every significant factual claim in product answers must be citable; never fabricate sources.
- Do not weaken safety to improve demos.
- Do not claim tests passed unless executed.
- Prefer transparent RAG pipeline code over heavy orchestration frameworks.

See [`AGENTS.md`](AGENTS.md) for the full rule set and mandatory handoff format.

---

## Workspace note

This project lives inside the `ai-portfolio` repository as `nutrition-knowledge-assistant/`. Git is managed at the portfolio root. Do not nest a separate git repository unless explicitly directed.

---

## Next step

**Agent 02 — Architecture** should produce system design and shared interfaces. See [`docs/handoffs/AGENT_01_HANDOFF.md`](docs/handoffs/AGENT_01_HANDOFF.md).
