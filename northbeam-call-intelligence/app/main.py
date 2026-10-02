"""HTTP layer. Thin on purpose: validation and rules live in app.service.

Run:  uv run uvicorn app.main:create_app --factory --port 8030
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

from app import __version__
from app.config import Settings
from app.demo import SCENARIOS, load_demo
from app.domain import ConflictError, NotFoundError, RequestError
from app.logging_setup import request_id, setup_logging
from app.service import CallService

STATIC = Path(__file__).resolve().parent / "static"
log = logging.getLogger("nci.http")


class ReviewIn(BaseModel):
    reviewer_id: str
    content_hash: str | None = None


def _consent(value: str | None) -> bool | None:
    if value is None or value.strip() == "" or value.strip().lower() in ("null", "none", "unknown"):
        return None
    if value.strip().lower() in ("true", "1", "yes"):
        return True
    if value.strip().lower() in ("false", "0", "no"):
        return False
    raise RequestError("consent_recorded must be true, false or empty")


def create_app(service: CallService | None = None) -> FastAPI:
    setup_logging()
    svc = service or CallService(Settings.from_env())
    app = FastAPI(title="Northbeam Call Intelligence", version=__version__)

    @app.middleware("http")
    async def with_request_id(request: Request, call_next: Any) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = request_id.set(rid)
        try:
            response: Response = await call_next(request)
        finally:
            request_id.reset(token)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(RequestError)
    async def _bad_request(_: Request, exc: RequestError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse({"detail": f"call {exc} not found"}, status_code=404)

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return svc.health()

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        return svc.metrics.render()

    @app.post("/v1/calls", status_code=201)
    def register_call(
        response: Response,
        external_id: str = Form(...),
        channel: str = Form(...),
        agent_id: str = Form(...),
        customer_company: str = Form(...),
        recorded_at: str = Form(...),
        consent_recorded: str | None = Form(None),
        language_hint: str | None = Form(None),
        audio_key: str | None = Form(None),
        process: bool = Form(True),
        file: UploadFile | None = File(None),
    ) -> dict[str, Any]:
        meta = {"external_id": external_id, "channel": channel, "agent_id": agent_id,
                "customer_company": customer_company, "recorded_at": recorded_at,
                "consent_recorded": _consent(consent_recorded),
                "language_hint": language_hint or None}
        limit = svc.policy.max_upload_mb * 1024 * 1024 + 1
        data = file.file.read(limit) if file is not None else None
        out = svc.register(meta, audio=data, filename=file.filename if file else None,
                           audio_key=audio_key or None, process=process)
        if out.get("idempotent"):
            response.status_code = 200
        return out

    @app.get("/v1/calls")
    def list_calls(status: str | None = None) -> list[dict[str, Any]]:
        return svc.list_calls(status)

    @app.get("/v1/calls/{call_id}")
    def get_call(call_id: str) -> dict[str, Any]:
        return svc.get(call_id)

    @app.post("/v1/calls/{call_id}/process")
    def process_call(call_id: str) -> dict[str, Any]:
        return svc.process(call_id)

    @app.post("/v1/calls/{call_id}/approve")
    def approve(call_id: str, body: ReviewIn) -> dict[str, Any]:
        return svc.decide(call_id, body.reviewer_id, "approve", body.content_hash)

    @app.post("/v1/calls/{call_id}/reject")
    def reject(call_id: str, body: ReviewIn) -> dict[str, Any]:
        return svc.decide(call_id, body.reviewer_id, "reject", body.content_hash)

    @app.delete("/v1/calls/{call_id}")
    def delete_call(call_id: str) -> dict[str, Any]:
        return svc.delete(call_id)

    @app.get("/v1/reports/daily")
    def daily_report(hours: int = 24) -> dict[str, Any]:
        return svc.daily_report(hours)

    @app.post("/v1/admin/retention/run")
    def retention() -> dict[str, Any]:
        return svc.run_retention()

    @app.get("/v1/demo/scenarios")
    def demo_scenarios() -> list[dict[str, Any]]:
        return SCENARIOS

    @app.post("/v1/demo/load")
    def demo_load() -> list[dict[str, Any]]:
        return load_demo(svc)

    return app
