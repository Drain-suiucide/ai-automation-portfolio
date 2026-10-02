# Northbeam Call Intelligence

> Sales-call audio in, CRM-safe actions out. The model is treated as an untrusted extractor: consent is checked first, personal data never reaches it, every claim must quote the transcript, and risk rules are plain code it cannot override.

**Status:** portfolio v0.1, reproducible demo. All data is synthetic and the default providers need no API keys.

## Why this project exists

Northbeam's sales team holds about 200 calls a week. Managers do not re-listen to recordings, CRM notes stay empty, and promises made to customers (discounts, deadlines) get lost.

After each call the service produces a transcript, a summary, action items with owners and dates, objections, commitments, risk flags and a follow-up draft. Anything risky (a discount above policy, churn signals, legal topics, text that tries to instruct the assistant) goes to a manager before anything is written to the CRM.

## Architecture

```
Audio (webhook or inbox folder)
        |
        v
 n8n 01-call-intake  ->  POST /v1/calls
        |
        v
  Consent gate --- no consent ---> blocked_no_consent (audio purged, nothing stored)
        |
        v
  ASR (fixture | faster-whisper)  ->  segments + speaker roles
        |
        v
  PII redaction   (before storage, logs and the model)
        |
        v
  LLM extraction  ->  evidence validator (drops every claim without proof)
        |
        v
  Policy engine (YAML, re-reads the transcript itself)
        |
   +----+-----------------+
   |                      |
 no flags              flags
   |                      |
 note + tasks         wait for a person: approve / reject
 written to CRM       (bound to the exact content hash)
   |                      |
   +----------+-----------+
              v
   Mock CRM  |  follow-up is a DRAFT, never sent

n8n: 02 daily digest, 03 retention sweeper, 99 error handler
SQLite: state and append-only, hash-chained audit  |  local blobs: audio
```

## What the demo proves

Press "Load demo scenarios" on the dashboard, or `POST /v1/demo/load`.

| Scenario | What happens |
|---|---|
| Discovery call with clear next steps | `analyzed`. Four action items, each linked to the sentence that produced it. Follow-up draft waits for approval. |
| Agent offers 25% (policy maximum 15%) | `pending_review`, flag `discount_over_policy`. Nothing is written to the CRM until a manager approves. |
| Customer threatens to cancel, names a competitor | `pending_review`, flag `churn_risk`. |
| Customer reads out a card, e-mail and phone | `analyzed`. Only `[CARD_1]`-style tokens reach the model, the database and the logs. |
| No recording announcement, no consent metadata | `blocked_no_consent`. Only a 60-second local probe ran; nothing was stored and the audio is purged. |
| Speech that tries to instruct the assistant | `pending_review`, flag `prompt_injection_suspected`. The text is treated as data; no CRM action changes. |
| Poor audio, almost no speech | `needs_manual_review`. No summary is invented. |
| Erasure request | `deleted`. Audio, text, insights and CRM records are gone; an audit tombstone with the content hash stays. |

## Run the demo

```bash
uv sync --extra dev
uv run uvicorn app.main:create_app --factory --port 8030
# open http://127.0.0.1:8030/
```

Upload your own file (the fixture ASR needs a prepared transcript named after `external_id`, see `evals/transcripts/`):

```bash
curl -F external_id=demo-discovery -F channel=phone -F agent_id=a-1 \
     -F customer_company="Acme" -F recorded_at=2026-09-29T10:00:00Z \
     -F consent_recorded= -F file=@call.wav http://127.0.0.1:8030/v1/calls
```

| Endpoint | Purpose |
|---|---|
| `POST /v1/calls` | Register a call (multipart file or `audio_key` from the inbox) and process it. Idempotent by `external_id` + file hash. |
| `GET /v1/calls`, `GET /v1/calls/{id}` | List calls; full detail with transcript, insights, flags, CRM actions and audit trail. |
| `POST /v1/calls/{id}/approve`, `/reject` | Decision by a named reviewer, bound to `review_hash`. A stale hash returns 409. |
| `DELETE /v1/calls/{id}` | Erase audio, text, insights and CRM records. |
| `GET /v1/reports/daily`, `POST /v1/admin/retention/run` | Digest and retention sweep (used by n8n). |
| `GET /health`, `GET /metrics` | Health with audit-chain check; Prometheus text. |

## Run n8n with PostgreSQL, Redis and two workers

```bash
cp .env.example .env        # set POSTGRES_PASSWORD and N8N_ENCRYPTION_KEY
docker compose up -d --build
```

Open http://localhost:5678, import `workflows/*.json`, and set each workflow's error workflow to `99 Error handler`. The Slack, Telegram and e-mail steps are labeled placeholders: connect your own credentials there.

## Real providers (optional)

```bash
uv sync --extra asr                     # local faster-whisper; stereo WAV: channel 0 agent, channel 1 customer
NCI_ASR_PROVIDER=faster_whisper NCI_LLM_PROVIDER=anthropic \
NCI_LLM_MODEL=<model id> NCI_LLM_API_KEY=<key> uv run uvicorn app.main:create_app --factory --port 8030
```

`openai`, `ollama` and `gateway` (an OpenAI-compatible endpoint, for example `northbeam-llm-gateway`) work the same way. Set `NCI_LLM_PRICE_IN_PER_M` and `NCI_LLM_PRICE_OUT_PER_M` to get cost per call in the audit trail and `/metrics`.

## Quality gate

```bash
uv run ruff check .
uv run mypy app scripts
uv run pytest -q
uv run python scripts/evaluate.py     # exits 1 if a hard gate fails
```

Seven invariants are covered by tests (`tests/test_inv_*.py`):

| Invariant | Guarantee |
|---|---|
| INV-1 | A call without consent never reaches full ASR or the model. |
| INV-2 | Raw personal data never appears in a prompt, the database or a log line (canary values). |
| INV-3 | A model claim without valid evidence never reaches the CRM. |
| INV-4 | There is no code that sends e-mail; follow-ups are drafts. |
| INV-5 | Speech is data: injected instructions change no action. |
| INV-6 | The model cannot remove or lower a policy flag. |
| INV-7 | After deletion no audio, text or insights remain; the audit tombstone does. |

Latest run on 30 synthetic calls (full report in `reports/evaluation.md`):

| Metric | Result |
|---|---|
| Status accuracy | 100% |
| Policy flags | recall 100%, precision 100% |
| Action items | precision 1.0, recall 1.0 |
| Hallucinated claims injected / dropped / leaked | 104 / 104 / 0 |
| Personal-data canaries leaked | 0 of 16 |
| Blocked calls that reached full ASR or the model | 0 |
| Follow-up drafts sent | 0 |

### Honest limits

Speech and labels come from the same templates, and the default extractor is a deterministic rule set. These numbers detect **regressions in the pipeline**; they say nothing about how a real model or real audio will perform. For a real deployment you need labeled recordings, per-field metrics, calibrated thresholds, and a WER measurement on your own audio (`scripts/measure_wer.py`). Latency in the report is pipeline overhead with a fixture ASR.

## Production boundary

What is intentionally not done in v0.1:

- No authentication or roles. Approvers are identified by a free-text id.
- SQLite and local files instead of PostgreSQL and S3/MinIO (`app/store.py` and `app/blobs.py` are the seams).
- Names are not redacted (a NER model such as Presidio is the next step).
- No real telephony, no real CRM adapter (only `mock`), no speaker diarization for mono audio beyond simple cues.
- The consent check for recordings without metadata needs a 60-second probe; see ADR 001.
- Consent and retention rules are configuration, not legal advice.

## Design decisions

- [001 Consent is checked before any processing](docs/adr/001-consent-gate.md)
- [002 Every model claim must point at the transcript](docs/adr/002-evidence-grounding.md)
- [003 Personal data is replaced before it can be sent, stored or logged](docs/adr/003-pii-before-llm.md)
- [004 A deterministic fake provider is the default](docs/adr/004-fake-provider-default.md)
- [005 A framework-free core, SQLite and local blobs](docs/adr/005-stdlib-core.md)

## Portfolio talking point

I treated the model as an untrusted extractor. Every claim must point to a transcript segment, personal data never reaches the model, consent is checked before any processing, and policy flags are deterministic code that a model output cannot override. n8n handles orchestration and retries; the typed service owns the business contract.
