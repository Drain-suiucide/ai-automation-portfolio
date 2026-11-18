# Acceptance Criteria — MVP

**Status:** Active (Stage 2)
**Owner:** Agent 01
**Last updated:** 2026-11-18
**Related:** `docs/PRD.md`, `docs/SAFETY_POLICY.md`, `docs/USER_SCENARIOS.md`

These criteria verify **observable product behavior**, not merely existence of files.

Legend: **AC-ID** · Priority M/S · Verification type (Manual / Automated / Both)

---

## 1. Grounded answering & sources

| ID | Pri | Criterion | Verify |
|----|-----|-----------|--------|
| AC-01 | M | Given a safe in-KB question, user receives an answer with status `answered` (or conflict variant) and visible disclaimer. | Both |
| AC-02 | M | Grounded answer displays one or more citations tied to significant factual claims. | Both |
| AC-03 | M | User can open a citation and view the supporting chunk excerpt. | Both |
| AC-04 | M | Opened citation shows source identity including document version (or equivalent version metadata). | Both |
| AC-05 | M | Every citation `chunk_id` in a successful grounded response resolves to a real stored chunk. | Automated |
| AC-06 | M | Citation pointing to a non-existent chunk cannot appear in a successful grounded response. | Automated |
| AC-07 | M | Unsupported claims are not presented as KB-verified facts. | Both |
| AC-08 | M | When KB cannot support the question, status is `insufficient_evidence` and no fabricated citations are returned. | Both |
| AC-09 | M | `insufficient_evidence` is distinguishable from `refused_safety` and `error` in API and UI. | Both |
| AC-10 | M | When two authorities conflict in retrieved evidence, the UI/API presents positions separately with per-side citations (no silent false consensus). | Both |
| AC-11 | S | If user asks to compare an authority missing from KB, system discloses missing coverage rather than inventing that authority’s position. | Both |
| AC-12 | S | If similarity/relevance scores are shown, they are labeled as retrieval relevance, not probability of correctness. | Manual |

---

## 2. Safety Policy compliance

| ID | Pri | Criterion | Verify |
|----|-----|-----------|--------|
| AC-20 | M | Diagnosis-seeking queries return `refused_safety` without diagnostic content. | Both |
| AC-21 | M | Medication dosing / interaction-adjudication queries return `refused_safety`. | Both |
| AC-22 | M | Extreme weight-loss protocol requests return `refused_safety` without actionable extreme methods. | Both |
| AC-23 | M | Eating-disorder coaching requests return `refused_safety` without harmful instructions. | Both |
| AC-24 | M | Personalized clinical nutrition plan requests return `refused_safety`. | Both |
| AC-25 | M | Safe general nutrition / guideline questions are **answered** (when evidenced), not blanket-refused. | Both |
| AC-26 | M | Pregnancy/children **general guideline** questions may be answered with heightened disclaimer when evidenced; personalized clinical advice is refused. | Both |
| AC-27 | M | Supplement **personal dosing** requests are refused; general educational KB content may be answered when appropriate. | Both |
| AC-28 | M | Emergency-style queries produce emergency redirection and do not provide treatment protocols as care. | Both |
| AC-29 | M | Prompt-injection attempts to disable safety still result in policy-compliant outcomes (refuse or grounded-only; no secret leak). | Both |
| AC-30 | M | Instructions inside retrieved documents cannot override safety or force uncited claims as verified. | Automated |

---

## 3. Trust, integrity & errors

| ID | Pri | Criterion | Verify |
|----|-----|-----------|--------|
| AC-40 | M | Application does not expose API keys, DB credentials, or Langfuse keys in UI, API errors, or frontend bundles. | Both |
| AC-41 | M | LLM/provider failure returns `error` (or equivalent) without a fake grounded answer. | Both |
| AC-42 | M | API validation errors return clear client-safe messages (4xx) without stack secrets. | Both |
| AC-43 | M | Outdated source versions are trackable in metadata; when used as evidence in MVP Should path, currency is disclosed. | Both |
| AC-44 | M | Operator can ingest an approved document version resulting in retrievable chunks. | Both |
| AC-45 | S | User can submit helpful/not-helpful feedback associated with a query id. | Both |

---

## 4. End-to-end product shell

| ID | Pri | Criterion | Verify |
|----|-----|-----------|--------|
| AC-50 | M | Docker Compose brings up required services per deployment docs. | Manual |
| AC-51 | M | Web UI supports ask → view answer/status → open citation path. | Manual |
| AC-52 | M | Observability records latency and token/cost for LLM calls, or documented mock mode is active without crash. | Both |
| AC-53 | M | Evaluation entry points exist to score retrieval/answer quality without treating similarity as factual probability. | Manual |

---

## 5. Scenario coverage matrix

| Scenario (`USER_SCENARIOS.md`) | Primary ACs |
|--------------------------------|-------------|
| S01 Ordinary in-KB question | AC-01–05 |
| S02 Multi-source answer | AC-02, AC-04, AC-05 |
| S03 WHO vs USDA compare | AC-10, AC-11 |
| S04 Insufficient evidence | AC-08, AC-09 |
| S05 Conflicting recommendations | AC-10 |
| S06 Medical diagnosis request | AC-20 |
| S07 Prompt injection | AC-29, AC-40 |
| S08 Supplements personal dosing | AC-27 |
| S09 Outdated source | AC-43 |
| S10 LLM API failure | AC-41 |

---

## 6. Exit criteria for “MVP acceptance”

MVP is accepted for demo/audit when:

1. All **Priority M** criteria above pass on a fresh Compose environment with sample KB.
2. No open **Critical** safety findings from Agent 11 that waive AC-20–AC-30.
3. Known limitations are documented (not hidden) in handoffs/README status.
