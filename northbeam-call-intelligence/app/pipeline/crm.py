"""CRM planning and providers. Only VALIDATED insights reach this module (INV-3).

There is deliberately no code anywhere in this project that sends e-mail (INV-4): the
follow-up is a draft that a human copies out after approval."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from app.domain import CRMAction, Flag, Insights

ALLOWED_KINDS = ("note", "task", "followup_draft")


def plan_actions(call_id: str, meta: dict[str, Any], insights: Insights,
                 flags: Sequence[Flag]) -> list[CRMAction]:
    review = any(f.severity == "review" for f in flags)
    status = "pending_manager_approval" if review else "stated_on_call"
    note = CRMAction("note", {
        "call_id": call_id,
        "company": meta.get("customer_company"),
        "summary": insights.summary,
        "sentiment": insights.sentiment,
        "objections": [{"type": o.type, "quote": o.quote} for o in insights.objections],
        "commitments": [{"kind": c.kind, "value_pct": c.value_pct, "who": c.who,
                         "quote": c.quote, "status": status} for c in insights.commitments],
        "competitors": list(insights.competitors),
        "flags": [f.code for f in flags if f.severity == "review"],
    }, requires_approval=review)
    tasks = [CRMAction("task", {
        "call_id": call_id, "text": a.text, "owner": a.owner, "due": a.due,
        "evidence": list(a.evidence)}, requires_approval=review) for a in insights.action_items]
    draft = CRMAction("followup_draft", {"call_id": call_id, "body_redacted": insights.followup_body},
                      requires_approval=True)
    return [note, *tasks, draft]


class CRMProvider(Protocol):
    name: str

    def execute(self, call_id: str, action: CRMAction) -> str: ...

    def forget(self, call_id: str) -> int: ...


class MockCRM:
    """In-memory CRM. `forget` models the erasure request propagated on DELETE."""

    name = "mock"

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def execute(self, call_id: str, action: CRMAction) -> str:
        ref = f"mock-crm-{len(self.records) + 1}"
        self.records.append({"ref": ref, "call_id": call_id, "kind": action.kind,
                             "payload": action.payload})
        return ref

    def forget(self, call_id: str) -> int:
        before = len(self.records)
        self.records = [r for r in self.records if r["call_id"] != call_id]
        return before - len(self.records)
