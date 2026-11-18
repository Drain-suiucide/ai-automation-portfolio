# Agent Workflow & Governance

**Status:** Active
**Owner:** Agent 00 (Project Bootstrap & Tech Lead)
**Last updated:** 2026-11-18

This document defines how specialized agents collaborate on Nutrition Knowledge Assistant without colliding on contracts or ownership.

---

## 1. Agent Roster (11 agents)

| ID | Role | Primary ownership |
|----|------|-------------------|
| **00** | Project Bootstrap & Tech Lead | Repo structure, charter, roadmap, decisions log, AGENTS.md, governance |
| **01** | Product Requirements | PRD, user stories, acceptance criteria, Safety Policy outline, UX requirements |
| **02** | Architecture | System design, module boundaries, shared interfaces, data model proposal, ADR-level architecture |
| **03** | Knowledge Sources | Source catalog, licensing, acquisition process, metadata standards for documents |
| **04** | Database & Infrastructure | PostgreSQL + pgvector schema, Alembic, Docker Compose, env config, migrations |
| **05** | Ingestion | Parse, normalize, chunk, embed, store pipeline |
| **06** | Retrieval | Query embedding, similarity search, ranking, retrieval API/service |
| **07** | Generation & Citations | Prompting, answer generation, citation attachment & validation, `insufficient_evidence` |
| **08** | Safety | Safety Policy implementation, classifiers/rules, refusal behavior |
| **09** | API & Frontend | FastAPI HTTP API, React/TS/Vite UI, end-to-end ask flow |
| **10** | Evaluation & Observability | Eval datasets, metrics, Langfuse instrumentation, quality reports |
| **11** | Independent Audit | Cross-cutting review of grounding, safety, contracts, DoD compliance |

> Note: Roadmap stage “Independent Audit” is Agent 11. Agents 00–10 deliver implementation stages; Agent 11 validates.

---

## 2. Dependency Graph

```
00 Bootstrap
 └─► 01 Product Requirements
      └─► 02 Architecture
           ├─► 03 Knowledge Sources
           ├─► 04 Database & Infrastructure
           │    └─► 05 Ingestion  ◄── 03 (source contracts)
           │         └─► 06 Retrieval
           │              └─► 07 Generation & Citations
           │                   └─► 08 Safety (may start in parallel after 02; must integrate before 09)
           └─► 09 API & Frontend  ◄── 06, 07, 08, 04
                └─► 10 Evaluation & Observability  ◄── 05–09
                     └─► 11 Independent Audit
```

**Parallelism rules:**

- 03 and 04 may proceed in parallel after 02 publishes interfaces.
- 08 may draft policy/implementation against 02 contracts in parallel with 05–07, but must not change generation contracts without RFC.
- 09 must not invent backend contracts; consume published OpenAPI / service interfaces.
- 10 must not change product behavior to “pass” evals; report gaps instead.
- 11 is read-mostly; may propose fixes via documented findings, not silent rewrites of ownership.

---

## 3. Work Order

1. Agent 00 completes bootstrap (this phase).
2. Agent 01 produces PRD + safety policy outline.
3. Agent 02 produces architecture + shared contracts.
4. Agents 03–04 execute in parallel where possible.
5. Agents 05 → 06 → 07 sequentially on the RAG core.
6. Agent 08 integrates safety into the answer path.
7. Agent 09 wires API + UI.
8. Agent 10 adds eval + observability.
9. Agent 11 audits and files findings.

An agent starts only when:

- required upstream deliverables exist;
- shared contracts for its inputs are documented;
- ownership boundaries are clear in this file and `AGENTS.md`.

---

## 4. File Ownership & Handoff Rules

### 4.1 Ownership

| Area | Owner |
|------|-------|
| `docs/PROJECT_CHARTER.md`, `docs/ROADMAP.md`, `docs/AGENT_WORKFLOW.md`, `docs/DECISIONS.md`, root `README.md`, `AGENTS.md` | Agent 00 (updates by later agents only via documented decision process) |
| `docs/PRD.md`, `docs/SAFETY_POLICY.md` (names may be refined by 01) | Agent 01 |
| `docs/ARCHITECTURE.md`, `docs/interfaces/*` | Agent 02 |
| `docs/sources/*`, `data/` curation manifests | Agent 03 |
| DB migrations, Compose, infra config | Agent 04 |
| Ingestion package/modules | Agent 05 |
| Retrieval package/modules | Agent 06 |
| Generation / citations package/modules | Agent 07 |
| Safety package/modules | Agent 08 |
| API routes, frontend app | Agent 09 |
| `evaluation/`, observability wiring | Agent 10 |
| Audit reports under `docs/audit/` | Agent 11 |

### 4.2 Allowed modifications

- An agent **may** create and edit files in its ownership area.
- An agent **may** add tests under `tests/` for its modules.
- An agent **must not** rewrite another agent’s core implementation without coordination.
- Cross-cutting docs (`DECISIONS.md`, shared interfaces) require the RFC process below.

### 4.3 Handoff packet (mandatory)

Every agent ends with a report containing at least:

1. Implementation Summary
2. Files Created
3. Files Modified
4. Technical Decisions
5. Tests (commands + actual results)
6. Known Limitations
7. Integration Contract
8. Next Agent Handoff

Store durable handoffs in `docs/handoffs/AGENT_XX_HANDOFF.md` when creating non-trivial deliverables.

---

## 5. Shared Contract Change Rules

Shared contracts include:

- HTTP API request/response schemas;
- DB tables/columns used across modules;
- retrieval result shapes;
- citation object schema;
- safety decision schema;
- evaluation dataset formats;
- environment variable names used by multiple services.

**Process:**

1. Propose change in `docs/DECISIONS.md` (or a linked ADR) **before** merging breaking edits.
2. State impact on dependent agents.
3. Update `docs/interfaces/*` (or Architecture doc) in the same change set.
4. Do not silently “fix” another module to compile against a private schema change.

If documentation for a needed contract does not exist yet: **do not invent a conflicting parallel contract**. Follow the project specification, document assumptions in the handoff, and flag blockers for Agent 02 / Tech Lead.

---

## 6. Testing Requirements

- Unit tests for new business logic.
- Integration tests when the module touches DB, external APIs, or multi-step pipelines.
- Tests must be runnable via documented commands (prefer `pytest`).
- Agents must **execute** relevant tests before claiming Done.
- Do not claim tests passed unless they were actually run; paste command + result summary.
- Safety and citation validation tests are mandatory for modules that affect answer content.

---

## 7. Git Rules

- Git is already initialized at the portfolio repository root (`ai-portfolio`). This project lives under `nutrition-knowledge-assistant/`.
- Do **not** create a nested `.git` inside this folder unless explicitly directed.
- Do **not** push or create remotes without user-provided remote / explicit request.
- Do **not** force-push shared branches.
- Commit only when the user asks.
- Prefer small, reviewable commits scoped to one agent’s deliverable.
- Never commit secrets (`.env`, keys, credentials).
- Never amend published history unless the user explicitly requests and conditions in project git rules are met.

---

## 8. Reporting & Definition of Done

A task is Done only when:

- implementation exists (or docs-only for bootstrap/requirements stages);
- required tests exist and have been executed (N/A only for pure documentation stages — state that explicitly);
- errors are handled;
- documentation is provided;
- interfaces are documented;
- limitations are disclosed;
- integration requirements are clear;
- mandatory final report is delivered.

---

## 9. Communication Norms Between Agents

- Prefer written contracts over chat assumptions.
- Prefer extending existing modules over duplicating services.
- Prefer refusal / `insufficient_evidence` over hallucinated completeness.
- Prefer safety compliance over demo polish.
