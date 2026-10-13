# Northbeam Lead Engine

> Turns a raw lead list into grounded, human-approved outreach drafts with send-time compliance guards — model writes sentences, rules decide who gets contacted.

**Status:** portfolio v0.1, reproducible demo. All data is synthetic. Mail goes to MailHog only.

## Why this project exists

SDR teams burn ~40 minutes researching each account, rewrite emails from scratch, and occasionally contact duplicates or suppressed addresses. This demo shows an outbound automation loop where:

- enrichment cites public (synthetic) sources;
- ICP score is deterministic code;
- every personalized claim is grounded;
- approval is bound to a content hash;
- guards re-run at send time so a late unsubscribe still wins.

## Architecture

```
CSV / webhook
    → n8n ingest → FastAPI import + dedupe + lawful_basis gate
    → enrich (fakeweb/nginx) → facts with sources
    → ICP score (YAML) → tier A/B/C
    → draft + grounding validator → approval queue
    → send-guard → SMTP (MailHog)
```

Providers: `EnrichmentProvider` (fakeweb), `LLMProvider` (fake by default), `MailProvider` (SMTP), `ApprovalChannel` (dashboard).

## What the demo proves

| Scenario | Expected |
|---|---|
| Clean tier-A lead | Grounded draft → approve → MailHog |
| Duplicate domain/email spelling | Auto-merge; no second send |
| `consent_required` country without consent | Block `country_policy` |
| Suppress after approve | Block at send (INV-3) |
| Edit after approve | `approval_hash_mismatch` |
| Injection on company page | `security_flag`, score/copy unchanged |
| robots/unavailable site | Neutral draft / `needs_data` |
| Double unsubscribe | Idempotent suppression |

## Run the demo

```bash
cd northbeam-lead-engine
cp .env.example .env
uv sync --extra dev
uv run python scripts/generate_leads.py
docker compose up -d postgres redis mailhog fakeweb
uv run uvicorn app.main:app --host 127.0.0.1 --port 8040
```

Open `http://127.0.0.1:8040/` → **Seed demo** → approve a draft → **Send batch**.

MailHog UI: `http://127.0.0.1:8025/`.

Full stack (including n8n workers + service container):

```bash
docker compose up -d
```

Service: `http://127.0.0.1:8040/` · n8n: `http://127.0.0.1:5678/` · MailHog: `http://127.0.0.1:8025/`.

## Run n8n with PostgreSQL, Redis and two workers

`docker-compose.yml` starts `n8n` in queue mode plus `n8n-worker-1` and `n8n-worker-2`. Import JSON from `workflows/` (no credentials embedded). Point HTTP nodes at `http://service:8040` inside Compose, or `http://127.0.0.1:8040` from the host.

## Quality gate

```bash
uv run ruff check .
uv run mypy app scripts
uv run pytest
uv run python scripts/evaluate.py
```

CI: `ai-portfolio/.github/workflows/lead-engine.yml` (path filter on this folder).

Metrics in `reports/evaluation.md` are **synthetic** and do not claim production quality.

## Compliance boundary

`app/config/country_policy.yml` is **illustrative only — not legal advice**. Obtain counsel before real outreach. Demo traffic never leaves MailHog.

## Production boundary

Not included: real ESP deliverability, social scraping, anti-bot bypass, paid enrichment, or live CRM writes. Optional `gateway` / HubSpot / Telegram providers are stubs for extension.

## Design decisions

See `docs/adr/`:

1. Deterministic scoring  
2. Send-time guards  
3. Hash-bound approval  
4. Fact grounding  

## Portfolio talking point

> The model writes sentences but never decides who gets contacted. Scoring and send rules are deterministic code, every personalized claim must cite a fetched source, approval is bound to the exact text hash, and all guards are re-evaluated at send time, so a late unsubscribe still wins.

## License / data

Synthetic companies and contacts only. No real emails, API keys, or tokens in the repo.
