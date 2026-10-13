from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.db import get_store
from app.models import ApprovalDecision, LawfulBasis, LeadImportRow
from app.providers import get_enrichment_provider, get_llm_provider, get_mail_provider
from app.service import (
    apply_approval,
    funnel_stats,
    import_csv,
    import_rows,
    run_draft,
    run_enrich_and_score,
    send_batch,
)
from app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("lead_engine")

app = FastAPI(title="Northbeam Lead Engine", version="0.1.0")
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class WebhookPayload(BaseModel):
    leads: list[LeadImportRow]


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Any) -> Any:
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    logger.info(
        '{"event":"request","method":"%s","path":"%s","request_id":"%s"}',
        request.method,
        request.url.path,
        rid,
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/leads/import")
async def leads_import(
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    store = get_store()
    text = (await file.read()).decode("utf-8")
    leads = import_csv(text, store)
    return {"imported": len(leads), "ids": [lead.id for lead in leads]}


@app.post("/v1/leads/webhook")
def leads_webhook(payload: WebhookPayload) -> dict[str, Any]:
    store = get_store()
    leads = import_rows(payload.leads, store)
    return {"imported": len(leads), "ids": [lead.id for lead in leads]}


@app.post("/v1/pipeline/enrich-score/{lead_id}")
def enrich_score(lead_id: str) -> dict[str, Any]:
    store = get_store()
    lead = store.get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    lead = run_enrich_and_score(lead, store, get_enrichment_provider())
    return lead.model_dump(mode="json")


@app.post("/v1/pipeline/draft/{lead_id}")
def draft_lead(lead_id: str) -> dict[str, Any]:
    store = get_store()
    lead = store.get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    lead = run_draft(lead, store, get_llm_provider())  # type: ignore[arg-type]
    return lead.model_dump(mode="json")


@app.post("/v1/pipeline/run-all")
def run_all() -> dict[str, Any]:
    store = get_store()
    enrichment = get_enrichment_provider()
    llm = get_llm_provider()
    processed = 0
    for lead in list(store.list_leads()):
        if lead.merged_into:
            continue
        run_enrich_and_score(lead, store, enrichment)
        run_draft(lead, store, llm)  # type: ignore[arg-type]
        processed += 1
    return {"processed": processed, "stats": funnel_stats(store)}


@app.get("/v1/leads")
def list_leads() -> list[dict[str, Any]]:
    return [lead.model_dump(mode="json") for lead in get_store().list_leads()]


@app.get("/v1/leads/{lead_id}")
def get_lead(lead_id: str) -> dict[str, Any]:
    lead = get_store().get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    return lead.model_dump(mode="json")


@app.get("/v1/approval/queue")
def approval_queue() -> list[dict[str, Any]]:
    store = get_store()
    out = []
    for lead in store.list_leads():
        if lead.state.value == "drafted" and lead.draft:
            out.append(lead.model_dump(mode="json"))
    return out


@app.post("/v1/approval/decision")
def approval_decision(decision: ApprovalDecision) -> dict[str, Any]:
    store = get_store()
    try:
        lead = apply_approval(decision, store)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return lead.model_dump(mode="json")


@app.post("/v1/send/batch")
def send_batch_endpoint(limit: int = 50) -> dict[str, Any]:
    store = get_store()
    mail = get_mail_provider()
    results = send_batch(store, mail, limit=limit)
    return {"results": results, "stats": funnel_stats(store)}


@app.api_route("/v1/unsubscribe/{token}", methods=["GET", "POST"])
def unsubscribe(token: str) -> PlainTextResponse:
    store = get_store()
    email = store.tokens.get(token)
    if not email:
        # idempotent-ish: unknown token still OK for privacy
        return PlainTextResponse("OK", status_code=200)
    store.add_suppression(email=email, reason="unsubscribe", token=token)
    domain = email.split("@")[-1]
    for lead in store.list_leads():
        if lead.email == email:
            from app.models import LeadState
            from app.state_machine import transition

            try:
                transition(lead, LeadState.UNSUBSCRIBED)
            except Exception:
                lead.state = LeadState.UNSUBSCRIBED
            store.upsert_lead(lead)
    store.append_audit("unsubscribed", email=email, domain=domain)
    return PlainTextResponse("You have been unsubscribed.", status_code=200)


@app.get("/v1/reports/weekly")
def weekly_report() -> dict[str, Any]:
    stats = funnel_stats(get_store())
    stats["cost_per_qualified_lead"] = 0.0  # fake LLM
    stats["note"] = "Synthetic demo metrics — not production quality claims."
    return stats


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    html_path = static_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Northbeam Lead Engine</h1><p>Dashboard missing.</p>")


@app.post("/v1/demo/seed")
def seed_demo(
    x_request_id: str | None = Header(default=None),
) -> dict[str, Any]:
    """Load bundled CSV and run pipeline for local demo."""
    _ = x_request_id
    store = get_store()
    csv_path = Path(__file__).resolve().parents[1] / "data" / "leads.csv"
    if not csv_path.exists():
        raise HTTPException(500, "data/leads.csv missing")
    leads = import_csv(csv_path.read_text(encoding="utf-8"), store)
    # Prefer static pages from data/fakeweb for offline enrichment
    pages: dict[str, str] = {}
    fakeweb = Path(__file__).resolve().parents[1] / "data" / "fakeweb"
    if fakeweb.exists():
        for about in fakeweb.glob("*/about.html"):
            pages[about.parent.name] = about.read_text(encoding="utf-8")
    enrichment = get_enrichment_provider(pages=pages)
    llm = get_llm_provider()
    for lead in leads:
        if lead.lawful_basis == LawfulBasis.UNKNOWN or lead.merged_into:
            continue
        run_enrich_and_score(lead, store, enrichment)
        run_draft(lead, store, llm)  # type: ignore[arg-type]
    return {"seeded": len(leads), "stats": funnel_stats(store)}


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=False)
