# EVALUATION_INTERFACE

**Owner:** Agent 10
**Module:** `app.modules.evaluation` + `evaluation/` runners
**FR/AC:** AC-53; supports AC-05–10, AC-20–30; NFR observability/reproducibility

---

## Purpose

Define how evaluation datasets, runs, and metrics are structured so retrieval quality, groundedness, citation validity/support, conflict handling, and safety behavior can be measured without treating similarity as factual probability.

---

## Concepts

| Concept | Definition |
|---------|------------|
| Dataset case | Fixed input + expected outcomes/labels |
| EvaluationRun | One execution of a suite |
| EvaluationResult | Per-case per-metric record |
| Deterministic check | Pure function of system artifacts (ids, statuses) |
| LLM-judge check | Explicitly labeled non-deterministic rubric |

---

## Dataset case schema (`evaluation/datasets/*.jsonl` conceptual)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `case_id` | string | yes | |
| `scenario_id` | string | no | e.g. `S01` |
| `question` | string | yes | |
| `expected_status` | enum | yes | one of five outcomes |
| `expected_refuse_categories` | string[] | no | |
| `relevant_chunk_ids` | UUID[] | no | for Recall@k |
| `must_cite_chunk_ids` | UUID[] | no | |
| `forbidden_behaviors` | string[] | no | e.g. `diagnosis`, `dosing` |
| `notes` | string | no | |

---

## Run request — `StartEvaluationRequest` (CLI or internal API)

| Field | Type | Required |
|-------|------|----------|
| `suite_name` | string | yes | e.g. `mvp_smoke` |
| `dataset_path` | string | yes | |
| `config` | object | yes | models, top_k, thresholds |
| `git_sha` | string \| null | no | |

### `EvaluationRun` output

| Field | Type | Required |
|-------|------|----------|
| `evaluation_run_id` | UUID | yes |
| `suite_name` | string | yes |
| `started_at` | string | yes |
| `finished_at` | string \| null | yes |
| `summary` | { metric: number } | yes | |

---

## Metric names (normative list)

| Metric | Type | Meaning |
|--------|------|---------|
| `outcome_accuracy` | deterministic | expected_status match |
| `citation_validity_rate` | deterministic | share of cites passing hard gate |
| `citation_hallucination_count` | deterministic | invalid cite attempts |
| `recall_at_k` | deterministic | labeled chunk retrieval |
| `safety_refusal_precision` | deterministic/hybrid | refuse when required |
| `safety_allow_recall` | deterministic | educational allows not over-refused |
| `conflict_disclosure_rate` | deterministic | S05-like cases |
| `groundedness_score` | LLM-judge/human | claims supported by evidence |
| `citation_support_score` | LLM-judge/human | cite entails claim |
| `latency_ms_p50` | operational | |
| `token_cost_usd_est` | operational | |

**Forbidden interpretation:** `relevance_score` average as `factual_accuracy`.

---

## `EvaluationResult` record

| Field | Type | Required |
|-------|------|----------|
| `evaluation_result_id` | UUID | yes |
| `evaluation_run_id` | UUID | yes |
| `case_id` | string | yes |
| `metric_name` | string | yes |
| `metric_value` | number | yes |
| `passed` | bool \| null | yes | |
| `details_json` | object | yes | sanitized |

### Example

```json
{
  "evaluation_result_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  "evaluation_run_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
  "case_id": "S04_insufficient",
  "metric_name": "outcome_accuracy",
  "metric_value": 1.0,
  "passed": true,
  "details_json": {"expected": "insufficient_evidence", "actual": "insufficient_evidence"}
}
```

---

## Error conditions

- Missing dataset → fail run startup.
- System `error` rate high → record metrics; do not fabricate passes.
- LLM-judge failure → mark metric `passed=null` with error detail; do not silently score 1.0.

---

## Dependencies

- QUERY_INTERFACE (or in-process orchestrator)
- DATA_MODEL EvaluationRun/Result
- Langfuse optional for attaching run ids

Must not modify production answers to “pass” evals (Agent Workflow rule).
