from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.models import AuditEvent, Lead, SuppressionEntry, utcnow
from app.settings import get_settings


class Store:
    """File-backed store for demos (no Postgres required for local pytest)."""

    def __init__(self, path: str | None = None) -> None:
        settings = get_settings()
        self.path = Path(path or settings.store_path)
        self._lock = threading.RLock()
        self.leads: dict[str, Lead] = {}
        self.audit: list[AuditEvent] = []
        self.suppressions: list[SuppressionEntry] = []
        self.tokens: dict[str, str] = {}
        self.sends_today: int = 0
        self.domain_sends: dict[str, int] = {}
        self.contacted_at: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.leads = {k: Lead.model_validate(v) for k, v in raw.get("leads", {}).items()}
        self.audit = [AuditEvent.model_validate(x) for x in raw.get("audit", [])]
        self.suppressions = [
            SuppressionEntry.model_validate(x) for x in raw.get("suppressions", [])
        ]
        self.tokens = dict(raw.get("tokens", {}))
        self.sends_today = int(raw.get("sends_today", 0))
        self.domain_sends = dict(raw.get("domain_sends", {}))
        self.contacted_at = dict(raw.get("contacted_at", {}))

    def persist(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, Any] = {
                "leads": {k: v.model_dump(mode="json") for k, v in self.leads.items()},
                "audit": [a.model_dump(mode="json") for a in self.audit],
                "suppressions": [s.model_dump(mode="json") for s in self.suppressions],
                "tokens": self.tokens,
                "sends_today": self.sends_today,
                "domain_sends": self.domain_sends,
                "contacted_at": self.contacted_at,
            }
            self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert_lead(self, lead: Lead) -> Lead:
        with self._lock:
            lead.touch()
            self.leads[lead.id] = lead
            self.persist()
            return lead

    def get_lead(self, lead_id: str) -> Lead | None:
        return self.leads.get(lead_id)

    def list_leads(self) -> list[Lead]:
        return list(self.leads.values())

    def append_audit(self, action: str, lead_id: str | None = None, **detail: Any) -> AuditEvent:
        event = AuditEvent(action=action, lead_id=lead_id, detail=detail, at=utcnow())
        with self._lock:
            self.audit.append(event)
            self.persist()
        return event

    def is_suppressed(self, email: str, domain: str) -> bool:
        email_l = email.strip().lower()
        domain_l = domain.strip().lower()
        for s in self.suppressions:
            if s.email and s.email.lower() == email_l:
                return True
            if s.domain and s.domain.lower() == domain_l:
                return True
        return False

    def add_suppression(
        self,
        *,
        email: str | None = None,
        domain: str | None = None,
        reason: str,
        token: str | None = None,
    ) -> SuppressionEntry:
        email_l = email.strip().lower() if email else None
        domain_l = domain.strip().lower() if domain else None
        with self._lock:
            for existing in self.suppressions:
                if email_l and existing.email == email_l:
                    return existing
                if domain_l and existing.domain == domain_l and not email_l:
                    return existing
            entry = SuppressionEntry(
                email=email_l, domain=domain_l, reason=reason, token=token
            )
            self.suppressions.append(entry)
            self.persist()
            return entry

    def reset(self) -> None:
        with self._lock:
            self.leads.clear()
            self.audit.clear()
            self.suppressions.clear()
            self.tokens.clear()
            self.sends_today = 0
            self.domain_sends.clear()
            self.contacted_at.clear()
            self.persist()


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def reset_store(path: str | None = None) -> Store:
    global _store
    import tempfile

    if path is None or path == ":memory:":
        tmp = Path(tempfile.gettempdir()) / "northbeam-lead-engine-test-store.json"
        _store = Store(path=str(tmp))
        _store.reset()
        return _store
    _store = Store(path=path)
    return _store
