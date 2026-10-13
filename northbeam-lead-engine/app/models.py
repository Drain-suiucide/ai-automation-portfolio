from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


class LawfulBasis(StrEnum):
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT = "consent"
    UNKNOWN = "unknown"


class LeadState(StrEnum):
    IMPORTED = "imported"
    NEEDS_BASIS = "needs_basis"
    DEDUPED = "deduped"
    ENRICHED = "enriched"
    SCORED = "scored"
    DRAFTED = "drafted"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    NURTURE = "nurture"
    ARCHIVED = "archived"
    NEEDS_DATA = "needs_data"
    NEEDS_DEDUP_REVIEW = "needs_dedup_review"


ALLOWED_TRANSITIONS: dict[LeadState, set[LeadState]] = {
    LeadState.IMPORTED: {
        LeadState.NEEDS_BASIS,
        LeadState.DEDUPED,
        LeadState.NEEDS_DEDUP_REVIEW,
        LeadState.ENRICHED,  # tests / direct enrich path
        LeadState.NEEDS_DATA,
    },
    LeadState.NEEDS_BASIS: {LeadState.IMPORTED},
    LeadState.NEEDS_DEDUP_REVIEW: {LeadState.DEDUPED, LeadState.IMPORTED},
    LeadState.DEDUPED: {LeadState.ENRICHED, LeadState.NEEDS_DATA},
    LeadState.ENRICHED: {LeadState.SCORED},
    LeadState.NEEDS_DATA: {LeadState.SCORED, LeadState.DRAFTED},
    LeadState.SCORED: {
        LeadState.DRAFTED,
        LeadState.NURTURE,
        LeadState.ARCHIVED,
    },
    LeadState.NURTURE: set(),
    LeadState.ARCHIVED: set(),
    LeadState.DRAFTED: {LeadState.APPROVED, LeadState.DRAFTED},
    LeadState.APPROVED: {LeadState.SENT, LeadState.DRAFTED},
    LeadState.SENT: {
        LeadState.REPLIED,
        LeadState.UNSUBSCRIBED,
        LeadState.BOUNCED,
    },
    LeadState.REPLIED: set(),
    LeadState.UNSUBSCRIBED: set(),
    LeadState.BOUNCED: set(),
}


class Fact(BaseModel):
    id: str
    type: str
    value: str
    source_url: str
    snippet: str
    fetched_at: datetime = Field(default_factory=utcnow)

    @field_validator("source_url")
    @classmethod
    def source_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("fact without source_url is forbidden")
        return v


class ScoreBreakdownItem(BaseModel):
    rule: str
    points: int


class DraftSentence(BaseModel):
    text: str
    fact_ids: list[str] = Field(default_factory=list)


class Draft(BaseModel):
    lead_id: str
    tier: Literal["A", "B", "C"]
    icp_score: int
    score_breakdown: list[ScoreBreakdownItem] = Field(default_factory=list)
    subject: str
    body: str
    sentences: list[DraftSentence] = Field(default_factory=list)
    content_hash: str = ""
    requires_approval: bool = True
    grounding: Literal["passed", "failed", "neutral"] = "neutral"
    fit_rationale: str = ""
    approved_hash: str | None = None
    approved_at: datetime | None = None
    original_body: str | None = None
    edited_body: str | None = None
    block_reason: str | None = None

    def recompute_hash(self, email: str) -> str:
        payload = f"{email.strip().lower()}|{self.subject}|{self.body}"
        digest = sha256(payload.encode("utf-8")).hexdigest()
        self.content_hash = f"sha256:{digest}"
        return self.content_hash


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: new_id("lead"))
    company: str
    domain: str
    contact_name: str
    email: str
    title: str = ""
    country: str = "US"
    source: str = "csv"
    collected_at: datetime = Field(default_factory=utcnow)
    lawful_basis: LawfulBasis = LawfulBasis.UNKNOWN
    state: LeadState = LeadState.IMPORTED
    canonical_domain: str = ""
    canonical_email: str = ""
    canonical_company: str = ""
    merged_into: str | None = None
    facts: list[Fact] = Field(default_factory=list)
    icp_score: int = 0
    tier: Literal["A", "B", "C"] | None = None
    score_breakdown: list[ScoreBreakdownItem] = Field(default_factory=list)
    draft: Draft | None = None
    security_flag: bool = False
    archive_reason: str | None = None
    timezone: str = "UTC"
    size_hint: int | None = None
    industry: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def touch(self) -> None:
        self.updated_at = utcnow()


class LeadImportRow(BaseModel):
    company: str
    domain: str
    contact_name: str
    email: str
    title: str = ""
    country: str = "US"
    source: str = "csv"
    collected_at: datetime | None = None
    lawful_basis: LawfulBasis = LawfulBasis.UNKNOWN


class ApprovalDecision(BaseModel):
    lead_id: str
    action: Literal["approve", "edit", "reject", "suppress"]
    edited_body: str | None = None
    edited_subject: str | None = None


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: new_id("audit"))
    at: datetime = Field(default_factory=utcnow)
    action: str
    lead_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class SuppressionEntry(BaseModel):
    email: str | None = None
    domain: str | None = None
    reason: str
    token: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class SendResult(BaseModel):
    lead_id: str
    sent: bool
    reason: str | None = None
    message_id: str | None = None
