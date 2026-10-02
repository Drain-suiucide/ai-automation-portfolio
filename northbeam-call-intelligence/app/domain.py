"""Plain, immutable domain objects. No framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SPEAKERS = ("agent", "customer", "unknown")
CHANNELS = ("phone", "meeting")
SENTIMENTS = ("positive", "neutral", "negative")


class Status(str, Enum):
    RECEIVED = "received"
    BLOCKED_NO_CONSENT = "blocked_no_consent"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"
    ANALYZED = "analyzed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"


class RequestError(ValueError):
    """The caller sent something invalid (HTTP 400/422)."""


class NotFoundError(LookupError):
    """Unknown call id (HTTP 404)."""


class ConflictError(RuntimeError):
    """State or hash conflict (HTTP 409)."""


@dataclass(frozen=True)
class Segment:
    id: str
    start: float
    end: float
    speaker: str
    text: str
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "start": self.start, "end": self.end,
                "speaker": self.speaker, "text": self.text, "confidence": self.confidence}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Segment:
        speaker = d.get("speaker", "unknown")
        if speaker not in SPEAKERS:
            speaker = "unknown"
        conf = d.get("confidence")
        return Segment(
            id=str(d["id"]),
            start=float(d["start"]),
            end=float(d["end"]),
            speaker=speaker,
            text=str(d["text"]),
            confidence=None if conf is None else float(conf),
        )


@dataclass(frozen=True)
class ActionItem:
    text: str
    owner: str
    due: str | None
    evidence: tuple[str, ...]
    quote: str


@dataclass(frozen=True)
class Objection:
    type: str
    evidence: tuple[str, ...]
    quote: str


@dataclass(frozen=True)
class Commitment:
    kind: str
    value_pct: int | None
    who: str
    evidence: tuple[str, ...]
    quote: str


@dataclass(frozen=True)
class Insights:
    summary: str
    sentiment: str
    action_items: tuple[ActionItem, ...] = ()
    objections: tuple[Objection, ...] = ()
    commitments: tuple[Commitment, ...] = ()
    competitors: tuple[str, ...] = ()
    followup_body: str = ""

    def to_dict(self, include_followup: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "summary": self.summary,
            "sentiment": self.sentiment,
            "action_items": [
                {"text": a.text, "owner": a.owner, "due": a.due,
                 "evidence": list(a.evidence), "quote": a.quote} for a in self.action_items],
            "objections": [
                {"type": o.type, "evidence": list(o.evidence), "quote": o.quote}
                for o in self.objections],
            "commitments": [
                {"kind": c.kind, "value_pct": c.value_pct, "who": c.who,
                 "evidence": list(c.evidence), "quote": c.quote} for c in self.commitments],
            "competitors": list(self.competitors),
        }
        if include_followup:
            out["followup_body"] = self.followup_body
        return out


@dataclass(frozen=True)
class Flag:
    code: str
    reason: str
    severity: str  # "review" forces a manager decision, "info" is informational
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "reason": self.reason, "severity": self.severity,
                "evidence": list(self.evidence)}


@dataclass(frozen=True)
class CRMAction:
    kind: str  # "note" | "task" | "followup_draft"
    payload: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False


@dataclass(frozen=True)
class ValidationReport:
    proposed: int
    kept: int
    dropped: dict[str, int]
    ignored_keys: tuple[str, ...] = ()
    normalized: tuple[str, ...] = ()

    @property
    def dropped_total(self) -> int:
        return sum(self.dropped.values())

    def to_dict(self) -> dict[str, Any]:
        return {"proposed": self.proposed, "kept": self.kept, "dropped": dict(self.dropped),
                "ignored_keys": list(self.ignored_keys), "normalized": list(self.normalized)}
