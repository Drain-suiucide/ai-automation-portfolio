# Product Requirements Document — Nutrition Knowledge Assistant

**Status:** Active (Stage 2)  
**Owner:** Agent 01 (Product Requirements & AI Safety)  
**Last updated:** 2026-11-18  
**Depends on:** `docs/PROJECT_CHARTER.md`, `docs/DECISIONS.md`, `docs/handoffs/AGENT_00_HANDOFF.md`

---

## 1. Product Vision

### 1.1 What it is

Nutrition Knowledge Assistant is a **RAG-based informational web application** that answers general nutrition questions using a **curated, versioned knowledge base** of official recommendations and scientific publications.

It is a demonstration system for **grounded, citeable nutrition information** — not a clinic, diagnostic engine, or treatment planner.

### 1.2 Problem

Public nutrition information is often unverifiable, marketing-driven, or framed as medical advice without evidence trails. Users cannot easily check which passage of which official document supports a claim, nor whether the system is inventing sources.

### 1.3 Value

Users receive answers that are:

1. **Grounded** in retrieved knowledge-base evidence;
2. **Citeable** to exact chunks and document versions;
3. **Honest** when evidence is insufficient (`insufficient_evidence`);
4. **Bounded** by an explicit Safety Policy;
5. **Auditable** for reviewers (citations, traces, evals).

### 1.4 Differentiation from a generic LLM chatbot

| Generic LLM chatbot | Nutrition Knowledge Assistant |
|---------------------|-------------------------------|
| Answers from parametric/world knowledge | Answers constrained to curated KB evidence |
| Citations optional / often fabricated | Citations required for significant claims; must resolve to real chunks + versions |
| Silent guessing when unsure | Explicit `insufficient_evidence` |
| Weak/no medical boundary enforcement | Testable Safety Policy with refusals |
| Opaque “helpful” tone | Transparent RAG pipeline; similarity ≠ factual probability |
| No document versioning | Versioned sources; outdated docs tracked |

---

## 2. Personas

| ID | Persona | Goals | Constraints / risks |
|----|---------|-------|---------------------|
| P1 | **Curious adult** | Everyday questions (food groups, nutrients, guidelines) | May over-trust AI; needs clear “not medical advice” framing |
| P2 | **Student / learner** | Study official recommendations with checkable sources | Needs chunk-level evidence for assignments/learning |
| P3 | **Health-conscious self-researcher** | Compare guidelines (e.g., WHO vs USDA) | May seek personalization; must stay non-clinical |
| P4 | **Caregiver / parent (non-clinical)** | General age-group dietary guideline info | High sensitivity for children/pregnancy; safety gates |
| P5 | **Product / AI engineer** | Inspect grounded RAG behavior, citations, eval hooks | Needs observability, reproducible pipelines |
| P6 | **Knowledge-base operator / curator** | Ingest approved sources, track versions, review failures | Needs admin/ops paths without end-user auth complexity in MVP |
| P7 | **Auditor / reviewer** | Verify grounding, safety refusals, no secret leakage | Needs acceptance criteria and threat mitigations |

Primary UX focus for MVP end-users: **P1–P3**. P6 uses operator tooling (CLI/scripts/docs acceptable for MVP). P5/P7 consume docs, evals, and traces.

---

## 3. User Stories

Each story includes acceptance criteria (AC). Priority tags: **M** Must / **S** Should / **C** Could for MVP.

### Asking & answering

**US-01 (M)** As a curious adult, I want to ask a free-text nutrition question so that I get an evidence-grounded answer.  
AC: Question accepted via UI; response returned with status `answered` or documented alternative status; answer text present when answered.

**US-02 (M)** As a user, I want significant factual claims in the answer to be backed by citations so that I can verify them.  
AC: Each significant claim maps to ≥1 citation object; UI shows citation markers.

**US-03 (M)** As a user, I want the system to refuse inventing KB-backed facts when evidence is missing so that I am not misled.  
AC: When evidence insufficient → status `insufficient_evidence`; no fabricated citations.

**US-04 (M)** As a user, I want a clear disclaimer that content is informational, not medical advice.  
AC: Disclaimer visible in UI (session/answer context); API metadata includes informational disclaimer flag/text.

**US-05 (S)** As a user, I want short clarifying questions only when needed for ambiguous safe queries.  
AC: Ambiguous safe query may return `needs_clarification` without providing unsafe personalization; MVP may defer multi-turn — if deferred, document as Won't Have and treat as single-turn only.

### Sources & citations

**US-06 (M)** As a learner, I want to open a citation and see the supporting chunk text so that I can verify the claim.  
AC: Citation resolves to chunk_id + document_version; UI shows chunk excerpt and source metadata.

**US-07 (M)** As a learner, I want to see source title, publisher/authority, and version/date so that I know provenance.  
AC: Citation/source panel shows title, authority (if known), version or publication date.

**US-08 (M)** As a reviewer, I want citations to fail validation if they point to non-existent chunks so that hallucinated citations never ship.  
AC: Invalid citation IDs rejected before user-facing `answered` response; logged.

**US-09 (S)** As a user, I want to navigate from a citation to document-level metadata (not only the chunk).  
AC: Document id/title/version accessible from citation detail.

**US-10 (S)** As a user, I want retrieval similarity scores (if shown) labeled as relevance, not correctness probability.  
AC: Any displayed score uses wording like “retrieval relevance”; never “probability true”.

### Comparing official recommendations

**US-11 (M)** As a self-researcher, I want to ask how two official sources compare on a topic (e.g., WHO vs USDA) so that differences are visible.  
AC: If both sources retrieved, answer presents positions separately with citations per source; does not invent a false consensus.

**US-12 (M)** As a user, I want conflicting recommendations presented as conflict, not merged into one prescription.  
AC: Status includes conflict signal (e.g., `answered_with_conflicts` or structured conflict section); each side cited.

**US-13 (S)** As a user, I want the system to state when only one of the requested authorities is in the KB.  
AC: Partial coverage disclosed; missing authority not fabricated.

### Insufficient evidence & contradictions

**US-14 (M)** As a user, I want an explicit insufficient-evidence outcome when the KB cannot support an answer.  
AC: `insufficient_evidence` returned; no pseudo-helpful guessed facts presented as verified.

**US-15 (M)** As a user, I want low retrieval relevance to be distinguishable from “model refuses for safety”.  
AC: Distinct statuses: at least `insufficient_evidence` vs `refused_safety` (exact enum by Architecture).

**US-16 (S)** As a reviewer, I want conflicting chunks on the same claim to be detectable in the response structure.  
AC: Conflicts listed with citations; generation does not silently pick one side without disclosure.

### Safety-sensitive intents

**US-17 (M)** As a user asking for a diagnosis, I want a refusal with safe redirection, not a diagnosis.  
AC: Matches Safety Policy category rules; status `refused_safety`; no diagnosis text.

**US-18 (M)** As a user asking for medication dosing or drug–nutrient treatment plans, I want refusal.  
AC: Refusal per Safety Policy; no dosing regimens.

**US-19 (M)** As a user asking for extreme/dangerous weight-loss methods, I want refusal and crisis-appropriate safe messaging where required.  
AC: Refusal; no instructional extreme methods; eating-disorder / crisis rules applied when triggered.

**US-20 (M)** As a caregiver asking general guideline questions about children or pregnancy (non-diagnostic), I want educational guideline content when allowed, not a blanket block of all related topics.  
AC: General guideline Q allowed with citations + heightened disclaimer; personalized clinical advice refused.

### Feedback & quality

**US-21 (S)** As a user, I want to mark an answer as helpful / not helpful so operators can improve eval sets.  
AC: Feedback captured (thumbs or equivalent) with query_id; stored or logged per Architecture.

**US-22 (C)** As a user, I want to report a bad citation (mismatch).  
AC: Report action creates structured feedback event linking citation_id.

**US-23 (S)** As an engineer, I want latency/token/cost traces for a query so that demos are measurable.  
AC: Langfuse (or documented mock) records request-level metrics.

### Knowledge-base administration

**US-24 (M)** As an operator, I want to ingest an approved document version into the KB so that retrieval can use it.  
AC: Document version stored; chunks + embeddings created; idempotency rules per Architecture documented.

**US-25 (M)** As an operator, I want each document to carry version/provenance metadata so citations remain auditable.  
AC: Required metadata fields enforced at ingest (schema by Agent 02/03).

**US-26 (S)** As an operator, I want outdated document versions flagged so answers can prefer or disclose currency.  
AC: `is_outdated` or equivalent tracked; behavior for outdated evidence defined (disclose at minimum).

**US-27 (S)** As an operator, I want to list ingested documents and versions.  
AC: Operator-facing list via API or documented CLI for MVP.

**US-28 (C)** As an operator, I want to deactivate a document version without deleting audit history.  
AC: Soft-deactivate supported; deactivated chunks excluded from default retrieval.

### Errors & resilience

**US-29 (M)** As a user, I want a clear error when the LLM API fails, without fake citations.  
AC: Status `error` (or equivalent); user-safe message; no invented answer presented as grounded.

**US-30 (M)** As a user, I want the app never to display API keys or internal secrets in errors or UI.  
AC: Error payloads sanitized; frontend bundle contains no secrets.

---

## 4. Functional Requirements

IDs are stable for Architecture and tests. Priority: M/S/C/W aligned with MoSCoW.

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-001 | M | System shall accept a user nutrition question via HTTP API and web UI. |
| FR-002 | M | System shall run safety classification on user intent before producing a grounded answer (exact pipeline order set by Architecture; must not be bypassable by retrieved text). |
| FR-003 | M | System shall retrieve relevant chunks from the curated KB for allowable queries. |
| FR-004 | M | System shall generate answers constrained to retrieved evidence for `answered*` statuses. |
| FR-005 | M | System shall attach citations to every significant factual claim in grounded answers. |
| FR-006 | M | System shall validate that each citation references an existing chunk_id and document_version. |
| FR-007 | M | System shall return `insufficient_evidence` when evidence cannot support a verified answer. |
| FR-008 | M | System shall return `refused_safety` (name exactable by Architecture) when Safety Policy requires refusal. |
| FR-009 | M | System shall not invent sources, document titles, or chunk IDs. |
| FR-010 | M | System shall not present parametric LLM knowledge as KB-verified fact. |
| FR-011 | M | System shall expose citation details sufficient to display chunk excerpt + source metadata in UI. |
| FR-012 | M | System shall support inspection of a cited chunk by identifier. |
| FR-013 | M | System shall treat retrieved document text as untrusted data (not instructions). |
| FR-014 | M | System shall present conflicting official recommendations separately with per-side citations when both are evidenced. |
| FR-015 | M | System shall disclose when a compared authority is missing from the KB rather than fabricate it. |
| FR-016 | M | System shall track document versions for all ingested sources. |
| FR-017 | M | System shall support operator ingestion of approved documents into versioned storage. |
| FR-018 | M | System shall persist chunks linked to document versions. |
| FR-019 | M | System shall store embeddings compatible with pgvector retrieval. |
| FR-020 | M | System shall return structured response status distinguishing answered / insufficient_evidence / refused_safety / error (minimum set). |
| FR-021 | M | System shall include an informational (non-medical-advice) disclaimer on user-facing answers. |
| FR-022 | M | System shall sanitize errors so secrets and stack internals are not leaked to clients. |
| FR-023 | M | System shall handle upstream LLM/embedding API failures with explicit error status. |
| FR-024 | M | UI shall render answer text, status, citations, and disclaimer. |
| FR-025 | M | UI shall allow opening a citation to view supporting fragment. |
| FR-026 | S | System shall mark or disclose outdated document versions when used as evidence. |
| FR-027 | S | System shall accept user feedback (helpful / not helpful) linked to a query id. |
| FR-028 | S | System shall allow operators to list documents and versions. |
| FR-029 | S | If similarity scores are exposed, UI/API labels them as retrieval relevance only. |
| FR-030 | S | System shall emit Langfuse traces for latency, tokens, and estimated cost (or documented mock mode). |
| FR-031 | C | System shall support soft-deactivation of document versions excluding them from default retrieval. |
| FR-032 | C | System shall accept structured “bad citation” reports. |
| FR-033 | M | System shall apply Safety Policy categories for supplements, meds, ED, extreme weight loss, pregnancy, children, emergencies (see `SAFETY_POLICY.md`). |
| FR-034 | M | System shall allow safe general nutrition / guidelines / scientific KB questions without over-refusing. |
| FR-035 | W | System shall not provide user accounts, social feeds, or open-web crawling in MVP. |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Measurable target (MVP local) |
|----|-------------|-------------------------------|
| NFR-P1 | End-to-end ask latency (p95) excluding cold start | ≤ 8 s for typical grounded query on local Compose with warm models/API |
| NFR-P2 | Chunk inspection endpoint | ≤ 500 ms p95 local (DB-backed, no LLM) |
| NFR-P3 | Retrieval stage | Completes within overall budget; target ≤ 1.5 s p95 local |

Targets are **local MVP SLOs**, not production SLAs. Architecture may refine.

### 5.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-R1 | LLM/provider failure yields controlled `error` response, not partial fake grounded answers. |
| NFR-R2 | DB unavailability yields controlled error; no silent empty “success”. |
| NFR-R3 | Ingestion failures are logged with document id and stage; partial corrupt writes avoided via transactional boundaries defined by Architecture. |

### 5.3 Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Secrets only via environment / secret store; never committed. |
| NFR-S2 | Prompt injection in user text or retrieved chunks must not override Safety Policy or system instructions. |
| NFR-S3 | Clients never receive API keys, Langfuse keys, or DB credentials. |
| NFR-S4 | MVP may be single-operator local deploy; if any admin endpoints exist, they must not be anonymously exposed without documented risk (AuthN deferred — see open questions). |

### 5.4 Scalability

| ID | Requirement |
|----|-------------|
| NFR-SC1 | MVP sized for demo/single-operator load (order of tens of concurrent requests not required). |
| NFR-SC2 | Data model must allow adding document versions without full DB rewrite. |
| NFR-SC3 | Horizontal scale-out of API is out of MVP; design should not preclude later scale. |

### 5.5 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-M1 | Clear module separation: API, ingest, retrieve, generate, cite, safety, eval, observability. |
| NFR-M2 | Shared contracts documented under Architecture interfaces. |
| NFR-M3 | Transparent RAG pipeline preferred over opaque mega-frameworks (per charter/decisions). |

### 5.6 Observability

| ID | Requirement |
|----|-------------|
| NFR-O1 | Per-request trace id correlating API → retrieve → generate. |
| NFR-O2 | Token usage and estimated cost recorded when LLM called. |
| NFR-O3 | Safety refusals and insufficient_evidence rates observable in logs/traces. |
| NFR-O4 | Missing Langfuse credentials must not crash the app (graceful degrade / mock mode documented). |

### 5.7 Reproducibility

| ID | Requirement |
|----|-------------|
| NFR-RP1 | Document version + chunk ids recorded for each citation used in a response. |
| NFR-RP2 | Evaluation datasets versioned under `evaluation/`. |
| NFR-RP3 | Model identifiers used for embed/generate recorded in traces or response metadata. |

### 5.8 Data integrity

| ID | Requirement |
|----|-------------|
| NFR-D1 | Citations cannot reference deleted/missing chunks in successful grounded responses. |
| NFR-D2 | Chunk always belongs to exactly one document version. |
| NFR-D3 | Ingest is idempotent for the same document version payload per Architecture rules. |
| NFR-D4 | Outdated flags do not delete historical versions needed for audit. |

---

## 6. Evidence & Trust Requirements

### 6.1 Mandatory rules

1. Every **significant factual claim** in a grounded answer must have evidentiary support from retrieved chunks.
2. Citations must reference **real chunk_ids** that exist in storage.
3. Sources must be **versioned**; citations include document version identity.
4. **Outdated** documents must be trackable; when used, currency must be disclosed (MVP minimum) or preferred-fresh policy applied if Architecture defines one.
5. **Contradictory** recommendations must be presented separately, each with citations — no silent synthesis into a single clinical prescription.
6. Lack of support → **`insufficient_evidence`**, not speculative filler marked as verified.
7. **Similarity score ≠ probability of factual correctness**; do not display or imply otherwise.

### 6.2 Concept distinctions (normative for product language)

| Term | Meaning | What it is not |
|------|---------|----------------|
| **Retrieval relevance** | How closely a chunk matches the query under the retrieval method (e.g., vector similarity) | Not proof the chunk is true or sufficient |
| **Factual correctness** | Whether a statement matches reality / authoritative science | Not automatically ensured by high similarity |
| **Groundedness** | Whether answer claims are supported by the provided retrieved evidence | Not the same as global factual correctness outside the KB |
| **Citation validity** | Citation identifiers resolve to real chunk + document version | Not proof the cited text actually supports the claim |
| **Citation support** | The cited chunk text actually entails / supports the claim | Stronger than validity alone; validation may be heuristic in MVP but must be pursued |

**Product rule:** Ship **citation validity** as hard gate for MVP. Measure **citation support** and **groundedness** in evaluation (Agent 10); improve support checks over time without claiming perfect NLI in MVP.

---

## 7. Language Policy (resolves Charter TBD)

| Decision | MVP rule |
|----------|----------|
| Primary UI/API language | English |
| Query language | English supported for MVP demos |
| Non-English queries | May return graceful unsupported/degraded message; full multilingual coverage **Won't Have** for MVP |
| Source language | Prefer English official sources for initial KB; non-English sources only if Agent 03 clears license + processing |

---

## 8. MVP Scope (MoSCoW)

### Must Have

- Ask → safety → retrieve → grounded generate → cite → validate citations → respond
- Statuses: answered (incl. conflict presentation), insufficient_evidence, refused_safety, error
- Citation inspect UX
- Versioned documents/chunks/embeddings
- Operator ingest path for approved sources
- Safety Policy enforcement for defined high-risk categories
- Disclaimer + no secret leakage
- Docker Compose local run
- Baseline eval hooks + Langfuse or mock
- English-only MVP language support

### Should Have

- Outdated source disclosure
- Operator document list
- User helpfulness feedback
- Partial coverage disclosure for multi-authority compare
- Relevance score labeling if scores exposed

### Could Have

- Soft-deactivate document versions
- Bad-citation report flow
- Multi-turn clarification

### Won't Have (MVP)

- Medical diagnosis / treatment / medication dosing / clinical personalization
- User accounts, social features, community KB edits
- Open-web crawling as knowledge source
- Full multilingual support
- Wearable/EHR integration
- Fine-tuned proprietary domain model (unless later Decision)
- Guaranteed clinical-grade factual correctness beyond KB grounding
- Production multi-tenant auth (unless Decision adds it)

---

## 9. Response Status Model (product-level)

Exact schema is Agent 02, but product requires these **outcomes** be distinguishable:

| Status (logical) | Meaning |
|------------------|---------|
| `answered` | Grounded answer with validated citations |
| `answered_with_conflicts` | Grounded answer disclosing conflicting sources |
| `insufficient_evidence` | Cannot support verified answer from KB |
| `refused_safety` | Blocked by Safety Policy |
| `error` | System/provider failure |

Optional later: `needs_clarification` (Could Have).

---

## 10. UX Requirements (high level)

1. Single primary ask composition: question input + submit.
2. Answer panel shows status, disclaimer, answer, citations.
3. Citation open → chunk excerpt + source/version metadata.
4. Conflict section visually separable when present.
5. Safety refusal copy is calm, non-dramatic, redirects to qualified professionals / emergency services when category requires.
6. Avoid card-heavy dashboard chrome; one job per view (ask / read answer / inspect evidence).
7. Do not show raw system prompts or secrets.

---

## 11. Open Questions for Agent 02 / later

See also `docs/handoffs/AGENT_01_HANDOFF.md`.

1. Exact safety placement order (pre-retrieve, post-generate, both).
2. AuthN for operator endpoints in local demo.
3. Thresholding for insufficient_evidence vs weak retrieval.
4. Depth of automated citation-support checking in MVP vs eval-only.
5. Whether `answered_with_conflicts` is separate status or flag on `answered`.

---

## 12. Traceability

| Artifact | Maps to |
|----------|---------|
| Charter success criteria | FR-005–008, FR-011–012, FR-020–021, NFR-O*, eval |
| Roadmap Stage 2 | This PRD + Safety Policy + Acceptance + Scenarios |
| Agent 08 | `docs/SAFETY_POLICY.md` |
| Agent 10 | Evidence definitions §6; NFRs observability/reproducibility |
| Agent 02 | Status model, schemas, pipeline order |
