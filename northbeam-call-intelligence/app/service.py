"""CallService: the use-case layer. Framework-free, so every invariant is unit-testable."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

from app.blobs import BlobError, LocalBlobStore, safe_name
from app.config import Policy, Settings, load_policy
from app.domain import (
    CHANNELS,
    ConflictError,
    CRMAction,
    Flag,
    NotFoundError,
    RequestError,
    Status,
)
from app.metrics import Metrics
from app.pipeline.asr import ASRError, ASRProvider, AudioRef, build_asr
from app.pipeline.consent import phrase_present
from app.pipeline.crm import CRMProvider, MockCRM, plan_actions
from app.pipeline.insights import SchemaError, build_insights
from app.pipeline.llm import LLMError, LLMProvider, build_llm, build_prompt
from app.pipeline.pii import redact_segments
from app.pipeline.policy import evaluate, requires_review
from app.pipeline.roles import assign_roles
from app.store import Store, dumps
from app.textutil import sha256_hex, word_count

log = logging.getLogger("nci.service")
_EXTERNAL_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
MAX_LLM_ATTEMPTS = 3  # first try + 2 retries (FR-7)
OPEN_STATUSES = (Status.ANALYZED.value, Status.PENDING_REVIEW.value)


@dataclass
class Providers:
    asr: ASRProvider
    llm: LLMProvider
    crm: CRMProvider


def build_providers(settings: Settings, policy: Policy) -> Providers:
    return Providers(build_asr(settings), build_llm(settings, policy), MockCRM())


def validate_meta(raw: dict[str, Any]) -> dict[str, Any]:
    ext = str(raw.get("external_id", "")).strip()
    if not _EXTERNAL_ID.match(ext):
        raise RequestError("external_id must be 1-128 chars of [A-Za-z0-9._:-]")
    channel = raw.get("channel")
    if channel not in CHANNELS:
        raise RequestError(f"channel must be one of {CHANNELS}")
    agent = str(raw.get("agent_id", "")).strip()
    company = str(raw.get("customer_company", "")).strip()
    if not agent or len(agent) > 64:
        raise RequestError("agent_id is required (max 64 chars)")
    if not company or len(company) > 120:
        raise RequestError("customer_company is required (max 120 chars)")
    rec = str(raw.get("recorded_at", "")).strip()
    try:
        dt = datetime.fromisoformat(rec.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RequestError("recorded_at must be an ISO 8601 date or datetime") from exc
    consent = raw.get("consent_recorded")
    if consent is not None and not isinstance(consent, bool):
        raise RequestError("consent_recorded must be true, false or null")
    lang = raw.get("language_hint")
    if lang is not None and (not isinstance(lang, str) or len(lang) > 8):
        raise RequestError("language_hint must be a short language code")
    return {"external_id": ext, "channel": channel, "agent_id": agent, "customer_company": company,
            "recorded_at": rec, "reference_date": dt.date().isoformat(),
            "consent_recorded": consent, "language_hint": lang or None}


class CallService:
    def __init__(self, settings: Settings, policy: Policy | None = None,
                 providers: Providers | None = None, metrics: Metrics | None = None) -> None:
        self.settings = settings
        self.policy = policy or load_policy(settings.policy_path)
        self.store = Store(settings.db_path)
        self.blobs = LocalBlobStore(settings.blob_dir)
        self.providers = providers or build_providers(settings, self.policy)
        self.metrics = metrics or Metrics()

    # ------------------------------------------------------------------ registration
    def register(self, meta_raw: dict[str, Any], audio: bytes | None = None,
                 filename: str | None = None, audio_key: str | None = None,
                 process: bool = True) -> dict[str, Any]:
        meta = validate_meta(meta_raw)
        if (audio is None) == (audio_key is None):
            raise RequestError("send either an audio file or an audio_key, not both or neither")
        try:
            if audio_key is not None:
                if not self.blobs.exists(audio_key):
                    raise RequestError("audio_key not found in the inbox")
                audio, filename = self.blobs.read(audio_key), audio_key
        except BlobError as exc:
            raise RequestError(str(exc)) from exc
        assert audio is not None
        ext = safe_name(filename or "audio.wav").rsplit(".", 1)[-1].lower()
        if ext not in self.policy.allowed_extensions:
            raise RequestError(f"unsupported audio format; allowed: {self.policy.allowed_extensions}")
        if not audio:
            raise RequestError("audio file is empty")
        if len(audio) > self.policy.max_upload_mb * 1024 * 1024:
            raise RequestError(f"audio exceeds {self.policy.max_upload_mb} MB")

        call, created = self.store.create_call(meta["external_id"], sha256_hex(audio), meta, ext)
        if not created:
            out = self.get(call["id"])
            out["idempotent"] = True
            return out
        self.blobs.put(call["audio_key"], audio)
        if audio_key is not None:
            self.blobs.delete_prefix(audio_key)
        self.store.audit(call["id"], "call_registered",
                         {"size_bytes": len(audio), "format": ext, "channel": meta["channel"]})
        if process:
            self.process(call["id"])
        out = self.get(call["id"])
        out["idempotent"] = False
        return out

    # -------------------------------------------------------------------- pipeline
    def process(self, call_id: str) -> dict[str, Any]:
        call = self._require(call_id)
        if call["status"] != Status.RECEIVED.value:
            raise ConflictError(f"call is {call['status']}; only 'received' calls can be processed")
        t0 = perf_counter()
        status, reason = self._run(call)
        self.store.update_call(call_id, status=status.value, status_reason=reason)
        self.store.audit(call_id, "processing_finished", {"status": status.value, "reason": reason})
        self.metrics.count_call(status.value)
        self.metrics.observe("total", perf_counter() - t0)
        log.info("call processed", extra={"fields": {"call_id": call_id, "status": status.value}})
        return self.get(call_id)

    def _run(self, call: dict[str, Any]) -> tuple[Status, str | None]:
        cid, meta, pol = call["id"], call["meta"], self.policy
        audio = AudioRef(meta["external_id"], self.blobs.path(call["audio_key"]),
                         Path(call["audio_key"]).name)
        asr = self.providers.asr

        # 1. consent gate (INV-1). consent=False never reaches ASR; consent=null runs a
        #    short local probe whose transcript is discarded, not stored.
        consent = meta.get("consent_recorded")
        if consent is False:
            self.store.audit(cid, "consent_checked", {"result": "blocked", "basis": "metadata"})
            self._purge_audio(call)
            return Status.BLOCKED_NO_CONSENT, "consent_declared_false"
        if consent is None:
            try:
                with self.metrics.stage("consent_probe"):
                    probe = asr.transcribe(audio, max_seconds=pol.consent_probe_seconds)
            except ASRError:
                self.store.audit(cid, "consent_checked", {"result": "error", "basis": "probe"})
                return Status.NEEDS_MANUAL_REVIEW, "consent_probe_failed"
            granted = phrase_present(probe.segments, pol)
            self.store.audit(cid, "consent_checked",
                             {"result": "granted" if granted else "blocked", "basis": "probe"})
            if not granted:
                self._purge_audio(call)
                return Status.BLOCKED_NO_CONSENT, "no_consent_phrase_in_probe"
        else:
            self.store.audit(cid, "consent_checked", {"result": "granted", "basis": "metadata"})

        # 2. transcription
        try:
            with self.metrics.stage("asr"):
                result = asr.transcribe(audio)
        except ASRError:
            return Status.NEEDS_MANUAL_REVIEW, "asr_failed"
        self.store.audit(cid, "asr_done", {
            "provider": result.meta.get("provider"), "segments": len(result.segments),
            "language": result.language,
            "avg_confidence": None if result.avg_confidence is None else round(result.avg_confidence, 3)})
        self.store.update_call(cid, language=result.language, asr_meta=result.meta)

        # 3. roles, then redaction BEFORE anything is stored, logged or sent to a model (INV-2)
        with self.metrics.stage("redact"):
            segments, counts = redact_segments(assign_roles(result.segments))
        self.store.audit(cid, "pii_redacted", {"counts": counts})
        if sum(word_count(s.text) for s in segments) < pol.min_words:
            self.store.save_transcript_only(cid, [s.to_dict() for s in segments])
            return Status.NEEDS_MANUAL_REVIEW, "too_short_or_silent"

        # 4. extraction with validation (retry on malformed output)
        prompt = build_prompt(segments, {"customer_company": meta["customer_company"],
                                         "channel": meta["channel"],
                                         "reference_date": meta["reference_date"]})
        insights = report = llm_meta = None
        for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
            try:
                with self.metrics.stage("llm"):
                    res = self.providers.llm.extract(prompt)
            except LLMError:
                self.store.audit(cid, "llm_called", {"attempt": attempt, "error": "provider_error"})
                continue
            self.store.audit(cid, "llm_called", {
                "attempt": attempt, "provider": res.provider, "model": res.model,
                "prompt_version": res.prompt_version, "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out, "cost_usd": round(res.cost_usd, 6)})
            self.metrics.add_llm(res.cost_usd, res.tokens_in + res.tokens_out)
            try:
                with self.metrics.stage("validate"):
                    insights, report = build_insights(res.raw_json, segments)
                llm_meta = {"provider": res.provider, "model": res.model,
                            "prompt_version": res.prompt_version}
                break
            except SchemaError:
                self.store.audit(cid, "llm_output_invalid", {"attempt": attempt})
        if insights is None or report is None or llm_meta is None:
            self.store.save_transcript_only(cid, [s.to_dict() for s in segments])
            return Status.NEEDS_MANUAL_REVIEW, "llm_output_invalid"
        self.metrics.count_dropped(report.dropped)

        # 5. deterministic policy, 6. CRM plan
        with self.metrics.stage("policy"):
            flags = evaluate(segments, insights, result.avg_confidence, report, pol)
        for f in flags:
            self.metrics.count_flag(f.code)
        self.store.audit(cid, "policy_flagged", {"codes": [f.code for f in flags]})
        review = requires_review(flags)
        rows = []
        for a in plan_actions(cid, meta, insights, flags):
            row = {"kind": a.kind, "payload": a.payload, "requires_approval": a.requires_approval,
                   "state": "pending_approval", "crm_ref": None}
            if not a.requires_approval:
                row["crm_ref"] = self.providers.crm.execute(cid, a)
                row["state"] = "executed"
            rows.append(row)
            self.store.audit(cid, "crm_action_created", {"kind": a.kind, "state": row["state"]})
        self.store.save_analysis(cid, [s.to_dict() for s in segments], insights.to_dict(),
                                 report.to_dict(), [f.to_dict() for f in flags], rows, llm_meta)
        return (Status.PENDING_REVIEW if review else Status.ANALYZED), None

    def _purge_audio(self, call: dict[str, Any]) -> None:
        self.blobs.delete_prefix(str(Path(call["audio_key"]).parent))
        self.store.audit(call["id"], "audio_purged", {"reason": "consent"})

    # ------------------------------------------------------------------- decisions
    def decide(self, call_id: str, reviewer_id: str, decision: str,
               content_hash: str | None = None) -> dict[str, Any]:
        if decision not in ("approve", "reject"):
            raise RequestError("decision must be approve or reject")
        reviewer_id = (reviewer_id or "").strip()
        if not reviewer_id or len(reviewer_id) > 64:
            raise RequestError("reviewer_id is required (max 64 chars)")
        call = self._require(call_id)
        if call["status"] not in OPEN_STATUSES:
            raise ConflictError(f"call is {call['status']}; nothing to {decision}")
        analysis = self.store.get_analysis(call_id)
        current = self.review_hash(analysis)
        if content_hash and content_hash != current:
            raise ConflictError("content changed since it was reviewed; reload and review again")
        for a in analysis["actions"]:
            if a["state"] != "pending_approval":
                continue
            if decision == "reject":
                self.store.set_action_state(a["id"], "cancelled")
            elif a["kind"] == "followup_draft":
                # Approved drafts are handed to a human. This project never sends e-mail (INV-4).
                self.store.set_action_state(a["id"], "approved_draft")
            else:
                ref = self.providers.crm.execute(
                    call_id, CRMAction(a["kind"], a["payload"], a["requires_approval"]))
                self.store.set_action_state(a["id"], "executed", ref)
        self.store.save_approval(call_id, reviewer_id, decision, current)
        status = Status.APPROVED if decision == "approve" else Status.REJECTED
        self.store.update_call(call_id, status=status.value)
        self.store.audit(call_id, "approved" if decision == "approve" else "rejected",
                         {"reviewer_id": reviewer_id, "content_hash": current})
        self.metrics.count_call(status.value)
        return self.get(call_id)

    @staticmethod
    def review_hash(analysis: dict[str, Any]) -> str:
        """Hash of exactly what a reviewer sees. Approvals are bound to it."""
        return sha256_hex(dumps({
            "insights": analysis["insights"], "flags": analysis["flags"],
            "actions": [[a["kind"], a["payload"]] for a in analysis["actions"]]}))

    # ---------------------------------------------------------- erasure & retention
    def delete(self, call_id: str, reason: str = "request") -> dict[str, Any]:
        call = self._require(call_id)
        if call["status"] == Status.DELETED.value:
            return self.get(call_id)
        removed = self.blobs.delete_prefix(str(Path(call["audio_key"]).parent)) if call["audio_key"] else 0
        self.store.erase_call_data(call_id)
        crm_removed = self.providers.crm.forget(call_id)
        self.store.update_call(call_id, status=Status.DELETED.value, meta={}, audio_key=None,
                               language=None, asr_meta={}, status_reason=reason,
                               deleted_at=datetime.now(UTC).isoformat(timespec="seconds"))
        self.store.audit(call_id, "deleted", {"content_hash": call["content_hash"], "reason": reason,
                                              "audio_files_removed": removed,
                                              "crm_records_removed": crm_removed})
        self.metrics.count_call(Status.DELETED.value)
        return self.get(call_id)

    def run_retention(self, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(UTC)
        cutoff = now - timedelta(days=self.settings.retention_days)
        deleted = []
        for c in self.store.list_calls():
            created = datetime.fromisoformat(c["created_at"])
            if c["status"] != Status.DELETED.value and created < cutoff:
                self.delete(c["id"], reason="retention")
                deleted.append(c["id"])
        return {"deleted": deleted, "cutoff": cutoff.isoformat(timespec="seconds")}

    # ----------------------------------------------------------------------- reads
    def _require(self, call_id: str) -> dict[str, Any]:
        call = self.store.get_call(call_id)
        if call is None:
            raise NotFoundError(call_id)
        return call

    def get(self, call_id: str) -> dict[str, Any]:
        call = self._require(call_id)
        analysis = self.store.get_analysis(call_id)
        review = [f for f in analysis["flags"] if f["severity"] == "review"]
        return {
            "id": call["id"], "external_id": call["external_id"], "status": call["status"],
            "status_reason": call["status_reason"], "meta": call["meta"],
            "language": call["language"], "created_at": call["created_at"],
            "deleted_at": call["deleted_at"], "content_hash": call["content_hash"],
            "requires_review": bool(review), **analysis,
            "review_hash": self.review_hash(analysis) if analysis["insights"] else None,
            "audit": [{"ts": e["ts"], "event": e["event"], "data": e["data"]}
                      for e in self.store.audit_events(call_id)],
        }

    def list_calls(self, status: str | None = None) -> list[dict[str, Any]]:
        return [{"id": c["id"], "external_id": c["external_id"], "status": c["status"],
                 "status_reason": c["status_reason"],
                 "customer_company": c["meta"].get("customer_company"),
                 "channel": c["meta"].get("channel"), "flags": c["flag_codes"],
                 "created_at": c["created_at"]} for c in self.store.list_calls(status)]

    def daily_report(self, hours: int = 24, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(UTC)
        since = now - timedelta(hours=hours)
        by_status: dict[str, int] = {}
        flags: dict[str, int] = {}
        dropped = proposed = 0
        pending = []
        for c in self.store.list_calls():
            if datetime.fromisoformat(c["created_at"]) < since:
                continue
            by_status[c["status"]] = by_status.get(c["status"], 0) + 1
            a = self.store.get_analysis(c["id"])
            for f in a["flags"]:
                if f["severity"] == "review":
                    flags[f["code"]] = flags.get(f["code"], 0) + 1
            if a["validation"]:
                dropped += sum(a["validation"]["dropped"].values())
                proposed += a["validation"]["proposed"]
            if c["status"] == Status.PENDING_REVIEW.value:
                pending.append({"id": c["id"], "company": c["meta"].get("customer_company"),
                                "flags": c["flag_codes"]})
        return {"window_hours": hours, "since": since.isoformat(timespec="seconds"),
                "calls": sum(by_status.values()), "by_status": by_status, "review_flags": flags,
                "pending_review": pending, "claims_proposed": proposed, "claims_dropped": dropped,
                "llm_cost_usd": round(self.metrics.cost_usd, 6)}

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "asr": self.providers.asr.name, "llm": self.providers.llm.name,
                "audit_chain_ok": self.store.verify_audit_chain()}


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


__all__ = ["CallService", "Providers", "build_providers", "validate_meta", "Flag"]
