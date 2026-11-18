# Project Charter — Nutrition Knowledge Assistant

**Status:** Draft (bootstrap)
**Owner:** Agent 00 (Project Bootstrap & Tech Lead)
**Last updated:** 2026-11-18

---

## 1. Purpose

Nutrition Knowledge Assistant is a RAG-based informational application that answers general nutrition questions using a curated knowledge base of official recommendations and scientific publications.

Every significant factual claim in an answer must be verifiable via citations that point to exact document fragments in a versioned knowledge base.

This product is a **demonstration system for grounded nutritional information**, not a clinical, diagnostic, or treatment tool.

---

## 2. Problem

General nutrition advice on the internet is often:

- unverifiable (no sources, or vague citations);
- mixed with marketing claims;
- presented as medical guidance without appropriate caveats;
- hard to audit for correctness and safety.

Users and reviewers need answers that are:

1. grounded in curated sources;
2. citeable to specific passages;
3. honest when evidence is insufficient;
4. bounded by clear safety rules.

---

## 3. Target Audience

| Audience | Need |
|----------|------|
| General users | Clear, cited answers to everyday nutrition questions |
| Students / learners | Verifiable explanations linked to sources |
| Product / AI engineers | Reference implementation of a transparent RAG pipeline |
| Reviewers / auditors | Traceable evidence trail for claims |

**Not** the primary audience: clinicians seeking decision-support for individual patients.

---

## 4. Core Value Proposition

> Ask a nutrition question → receive an evidence-grounded answer with citations to curated sources, or an explicit `insufficient_evidence` response when the knowledge base cannot support the claim.

Key differentiators:

- citations tied to chunk + document version;
- refusal of unsupported and unsafe content;
- transparent RAG pipeline (not a black-box “agent framework”);
- measurable retrieval and answer quality.

---

## 5. Primary User Scenarios

1. **General Q&A** — User asks about dietary guidelines, nutrients, food groups, or official recommendations; system returns a cited answer.
2. **Evidence inspection** — User opens a citation and views the supporting document fragment.
3. **Insufficient evidence** — Knowledge base lacks support; system returns `insufficient_evidence` instead of inventing content.
4. **Safety boundary** — User asks for diagnosis, treatment, medication dosing, or dangerous advice; system refuses per Safety Policy and provides general educational framing or redirection as specified.
5. **Operator evaluation** — Maintainer runs retrieval/answer evaluation suites and reviews quality metrics, latency, token usage, and cost.

---

## 6. MVP Scope

In scope for MVP:

1. Curated ingestion of approved nutrition sources.
2. Document parse → normalize → chunk → embed → store.
3. Semantic retrieval over pgvector-backed store.
4. Answer generation constrained to retrieved evidence.
5. Citation attachment and citation validation.
6. Safety checks for medical / vulnerable-user scenarios.
7. FastAPI backend + React/TypeScript web UI.
8. Observability via Langfuse (traces, latency, tokens, cost).
9. Baseline evaluation for retrieval and answer quality.
10. Docker Compose local deployment.

---

## 7. Out of Scope (MVP)

- Medical diagnosis or differential diagnosis.
- Personalized clinical nutrition prescriptions.
- Medication instructions or dosing.
- Continuous wearable / EHR integration.
- Multilingual full coverage (language policy TBD by Product Requirements).
- User accounts, social features, or community-generated content.
- Automatic crawling of the open web as a knowledge source.
- Fine-tuning proprietary domain models (unless later approved in DECISIONS.md).

---

## 8. Product Constraints

1. **Informational only** — not medical advice, diagnosis, or treatment.
2. **No invented sources** — LLM must not fabricate citations or present parametric knowledge as KB-verified.
3. **Retrieved content is untrusted data** — never execute or treat as instructions.
4. **Citation integrity** — every significant factual claim needs a valid citation to an existing chunk and document version.
5. **Safety over demo success** — do not weaken safety controls to improve demos.
6. **Secrets via environment** — no hardcoded API keys or credentials.
7. **Approved stack** — see `docs/DECISIONS.md`; architectural details owned by Agent 02.

---

## 9. Success Criteria

MVP is successful when:

| Criterion | Indicator |
|-----------|-----------|
| Groundedness | Significant factual claims are citation-backed; unsupported claims are refused |
| Citation validity | Citations resolve to real chunks + document versions |
| Safety | Policy-defined unsafe intents are refused |
| Usability | Web UI allows ask → answer → inspect citations |
| Measurability | Retrieval and answer evaluation can be run; latency/tokens/cost are tracked |
| Operability | Local Docker Compose brings up the stack with documented configuration |
| Transparency | Pipeline modules (ingest, retrieve, generate, cite, safety) are separable and documented |

---

## 10. Non-Goals for Bootstrap

This charter does **not** define API schemas, DB models, chunking algorithms, or prompt templates. Those belong to later agents (01–10) under the roadmap and shared contracts.
