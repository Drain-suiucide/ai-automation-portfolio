from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from app.db import Store
from app.models import Lead, LeadState
from app.pipeline.normalize import apply_normalization
from app.state_machine import transition


@dataclass
class DedupeDecision:
    action: str  # merge | review | keep
    score: float
    target_id: str | None = None


def similarity(a: Lead, b: Lead) -> float:
    email_score = 100.0 if a.canonical_email == b.canonical_email else 0.0
    domain_score = fuzz.ratio(a.canonical_domain, b.canonical_domain)
    company_score = fuzz.token_sort_ratio(a.canonical_company, b.canonical_company)
    # Weighted blend; exact email dominates.
    if email_score == 100.0:
        return 1.0
    return (0.45 * domain_score + 0.55 * company_score) / 100.0


def decide(a: Lead, b: Lead) -> DedupeDecision:
    score = similarity(a, b)
    if score >= 0.95:
        return DedupeDecision(action="merge", score=score, target_id=b.id)
    if score >= 0.80:
        return DedupeDecision(action="review", score=score, target_id=b.id)
    return DedupeDecision(action="keep", score=score)


def prepare_lead(lead: Lead) -> Lead:
    company, domain, email = apply_normalization(lead.company, lead.domain, lead.email)
    lead.canonical_company = company
    lead.canonical_domain = domain
    lead.canonical_email = email
    lead.domain = domain
    lead.email = email
    return lead


def dedupe_against_store(lead: Lead, store: Store) -> tuple[Lead, DedupeDecision | None]:
    lead = prepare_lead(lead)
    if lead.lawful_basis.value == "unknown":
        transition(lead, LeadState.NEEDS_BASIS)
        store.append_audit("needs_basis", lead.id, reason="lawful_basis=unknown")
        return lead, None

    best: DedupeDecision | None = None
    for other in store.list_leads():
        if other.id == lead.id or other.merged_into:
            continue
        decision = decide(lead, other)
        if best is None or decision.score > best.score:
            best = decision
        if decision.action == "merge" and decision.target_id:
            lead.merged_into = decision.target_id
            transition(lead, LeadState.DEDUPED)
            store.append_audit(
                "dedupe_merge",
                lead.id,
                target=decision.target_id,
                score=decision.score,
            )
            return lead, decision
        if decision.action == "review":
            transition(lead, LeadState.NEEDS_DEDUP_REVIEW)
            store.append_audit(
                "dedupe_review",
                lead.id,
                target=decision.target_id,
                score=decision.score,
            )
            return lead, decision

    transition(lead, LeadState.DEDUPED)
    store.append_audit("dedupe_keep", lead.id, score=best.score if best else 0.0)
    return lead, best
