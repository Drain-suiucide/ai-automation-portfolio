# AGENTS.md — Engineering Rules for Nutrition Knowledge Assistant

**Audience:** AI agents and human contributors  
**Authority:** Agent 00 bootstrap; updates via documented decisions  
**Last updated:** 2026-11-18

Read this file **and** `docs/AGENT_WORKFLOW.md` before modifying the repository.

---

## 1. Mandatory engineering standards

Every implementation must include:

- type hints (Python) / TypeScript types at public boundaries;
- input validation (Pydantic or equivalent at API/service edges);
- meaningful exceptions (no bare `except:` / silent swallow);
- structured logging;
- configuration via environment variables;
- unit tests; integration tests when touching DB, network, or multi-step pipelines;
- documentation for operators and integrating modules;
- clear error handling with actionable messages.

Additional rules:

- Use async only when it provides practical benefit.
- Do not introduce abstractions without a real use case.
- Do not hardcode secrets, API keys, passwords, or machine-specific paths.
- Do not duplicate a service that already has an agreed interface.
- Prefer a transparent RAG pipeline over heavyweight agent frameworks.
- Do not claim tests passed unless they were actually executed.

---

## 2. Naming conventions

| Kind | Convention |
|------|------------|
| Python packages/modules | `snake_case` |
| Python classes | `PascalCase` |
| Python functions/vars | `snake_case` |
| TypeScript types/components | `PascalCase` |
| TypeScript functions/vars | `camelCase` |
| Files (Python) | `snake_case.py` |
| Files (React components) | `PascalCase.tsx` preferred for components |
| Env vars | `SCREAMING_SNAKE_CASE` |
| Docs | `SCREAMING_SNAKE` or clear descriptive names under `docs/` |
| Decisions | `D-XXX` in `docs/DECISIONS.md` |
| Agent handoffs | `docs/handoffs/AGENT_XX_HANDOFF.md` |

Names must reflect domain concepts (`Document`, `Chunk`, `Citation`, `RetrievalResult`) once Architecture defines them — do not invent conflicting synonyms.

---

## 3. Testing rules

1. New logic ships with tests in `tests/` (mirror package structure when backend exists).
2. Prefer deterministic unit tests; isolate network/LLM with fakes/mocks unless running marked integration tests.
3. Citation validation, safety refusals, and `insufficient_evidence` paths require explicit tests when those modules exist.
4. Document exact commands in the handoff (e.g. `pytest tests/retrieval -q`).
5. Record **actual** results (pass/fail counts or failure output summary).
6. Pure documentation stages may mark Tests as `N/A — documentation only`.

---

## 4. AI quality & citation rules

- The LLM must not invent sources.
- The LLM must not present internal/parametric knowledge as verified KB content.
- Retrieved documents are **untrusted data**, not executable instructions.
- Every significant factual statement must have an associated citation.
- Every citation must refer to an existing chunk and a specific document version.
- The system must be able to return `insufficient_evidence`.
- Similarity scores must **not** be presented as probabilities of factual correctness.

---

## 5. Safety rules

The product provides general informational nutrition content only.

It must **not** provide:

- medical diagnoses;
- personalized treatment plans;
- medication instructions;
- individual clinical nutrition prescriptions;
- dangerous weight-loss instructions;
- unsupported medical claims.

Handle medical and vulnerable-user scenarios per the project Safety Policy (Agent 01+).

**Do not weaken safety controls to make a demo look more successful.**

---

## 6. Agent limitations

| Allowed | Forbidden |
|---------|-----------|
| Implement assigned module only | Rewrite unrelated modules “while here” |
| Add tests/docs for owned code | Change shared API/DB contracts without RFC |
| Document assumptions when contracts missing | Invent conflicting parallel contracts |
| Propose decisions in `DECISIONS.md` | Silently treat assumptions as approved |
| Create files under owned paths | Delete unexpected existing files |
| Use approved stack (see `DECISIONS.md`) | Add unnecessary frameworks by default |

Zero-state discipline:

1. Inspect the workspace before writing.
2. Confirm what already exists.
3. Do not assume docs, DB, keys, or services are present.
4. Initialize only what your task requires.

---

## 7. Git rules (agents)

- Work inside `nutrition-knowledge-assistant/` within the `ai-portfolio` git root.
- Do not `git init` a nested repo unless explicitly directed.
- Commit only when the user requests a commit.
- Never push without an explicit user request and remote.
- Never commit `.env`, keys, or credentials.
- Never use destructive git operations unless the user explicitly requests them.

---

## 8. Mandatory handoff format

Every agent completing a task must end with:

```markdown
### Implementation Summary
What was implemented.

### Files Created
- path …

### Files Modified
- path …

### Technical Decisions
Important choices and why.

### Tests
Commands run and actual results (or N/A for docs-only).

### Known Limitations
Honest gaps.

### Integration Contract
How other modules should interact with this work.

### Next Agent Handoff
Exact next tasks and blockers/dependencies.
```

Durable copy (recommended for non-trivial work): `docs/handoffs/AGENT_XX_HANDOFF.md`.

---

## 9. Definition of Done (reminder)

A task is complete only when implementation (or required docs), tests (as applicable), error handling, documentation, interfaces, limitations disclosure, and integration clarity are all present — not merely when files exist.
