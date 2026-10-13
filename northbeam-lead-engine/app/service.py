from __future__ import annotations

import csv
import io
from typing import Any

from app.db import Store
from app.models import (
    ApprovalDecision,
    LawfulBasis,
    Lead,
    LeadImportRow,
    LeadState,
)
from app.pipeline.dedupe import dedupe_against_store
from app.pipeline.draft import FakeLLM, build_draft, neutral_draft
from app.pipeline.enrich import EnrichmentProvider, enrich_lead
from app.pipeline.ground import validate_grounding
from app.pipeline.score import score_lead
from app.pipeline.send import MailProvider, send_lead
from app.state_machine import transition


def import_rows(rows: list[LeadImportRow], store: Store) -> list[Lead]:
    created: list[Lead] = []
    for row in rows:
        lead = Lead(
            company=row.company,
            domain=row.domain,
            contact_name=row.contact_name,
            email=row.email,
            title=row.title,
            country=row.country,
            source=row.source,
            lawful_basis=row.lawful_basis,
        )
        if row.collected_at:
            lead.collected_at = row.collected_at
        lead, _ = dedupe_against_store(lead, store)
        store.upsert_lead(lead)
        store.append_audit("imported", lead.id, source=row.source)
        created.append(lead)
    return created


def import_csv(text: str, store: Store) -> list[Lead]:
    reader = csv.DictReader(io.StringIO(text))
    rows: list[LeadImportRow] = []
    for raw in reader:
        rows.append(
            LeadImportRow(
                company=raw.get("company", "").strip(),
                domain=raw.get("domain", "").strip(),
                contact_name=raw.get("contact_name", "").strip(),
                email=raw.get("email", "").strip(),
                title=raw.get("title", "").strip(),
                country=raw.get("country", "US").strip() or "US",
                source=raw.get("source", "csv").strip() or "csv",
                lawful_basis=LawfulBasis(
                    raw.get("lawful_basis", "unknown").strip() or "unknown"
                ),
            )
        )
    return import_rows(rows, store)


def run_enrich_and_score(lead: Lead, store: Store, enrichment: EnrichmentProvider) -> Lead:
    if lead.state == LeadState.NEEDS_BASIS:
        return lead
    if lead.merged_into:
        return lead
    if lead.state not in {LeadState.DEDUPED, LeadState.NEEDS_DATA, LeadState.ENRICHED}:
        if lead.state == LeadState.IMPORTED:
            lead, _ = dedupe_against_store(lead, store)
            store.upsert_lead(lead)
        if lead.state == LeadState.NEEDS_BASIS:
            return lead

    enrich_lead(lead, enrichment, store)
    score_lead(lead, store)
    store.upsert_lead(lead)
    return lead


def run_draft(lead: Lead, store: Store, llm: FakeLLM | None = None) -> Lead:
    if lead.tier != "A" and lead.state not in {LeadState.SCORED, LeadState.NEEDS_DATA}:
        return lead
    if lead.state == LeadState.NURTURE or lead.state == LeadState.ARCHIVED:
        return lead

    if lead.state == LeadState.NEEDS_DATA or not lead.facts:
        lead.draft = neutral_draft(lead)
        transition(lead, LeadState.DRAFTED)
        store.upsert_lead(lead)
        return lead

    build_draft(lead, llm or FakeLLM(), store)
    assert lead.draft is not None
    validate_grounding(lead)
    store.upsert_lead(lead)
    return lead


def apply_approval(decision: ApprovalDecision, store: Store) -> Lead:
    lead = store.get_lead(decision.lead_id)
    if lead is None or lead.draft is None:
        raise KeyError("lead or draft not found")

    draft = lead.draft
    if decision.action == "reject":
        lead.archive_reason = "rejected"
        transition(lead, LeadState.ARCHIVED)
        store.append_audit("rejected", lead.id)
        store.upsert_lead(lead)
        return lead

    if decision.action == "suppress":
        store.add_suppression(email=lead.email, reason="manual_suppress")
        transition(lead, LeadState.UNSUBSCRIBED)
        store.append_audit("suppressed", lead.id)
        store.upsert_lead(lead)
        return lead

    if decision.action == "edit":
        if decision.edited_body:
            draft.edited_body = decision.edited_body
            draft.body = decision.edited_body
        if decision.edited_subject:
            draft.subject = decision.edited_subject
        draft.approved_hash = None
        draft.approved_at = None
        draft.recompute_hash(lead.email)
        transition(lead, LeadState.DRAFTED)
        store.append_audit("edited", lead.id, hash=draft.content_hash)
        store.upsert_lead(lead)
        return lead

    # approve
    draft.recompute_hash(lead.email)
    draft.approved_hash = draft.content_hash
    from app.models import utcnow

    draft.approved_at = utcnow()
    transition(lead, LeadState.APPROVED)
    store.append_audit("approved", lead.id, hash=draft.approved_hash)
    store.upsert_lead(lead)
    return lead


def send_batch(store: Store, mail: MailProvider, limit: int = 50) -> list[dict[str, Any]]:
    results = []
    approved = [
        lead for lead in store.list_leads() if lead.state == LeadState.APPROVED
    ]
    for lead in approved[:limit]:
        result = send_lead(lead, store, mail)
        results.append(result.model_dump())
    return results


def funnel_stats(store: Store) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for lead in store.list_leads():
        counts[lead.state.value] = counts.get(lead.state.value, 0) + 1
    blocks: dict[str, int] = {}
    for ev in store.audit:
        if ev.action == "send_blocked":
            reason = str(ev.detail.get("reason", "unknown"))
            blocks[reason] = blocks.get(reason, 0) + 1
    edits = sum(1 for ev in store.audit if ev.action == "edited")
    approvals = sum(1 for ev in store.audit if ev.action == "approved")
    edit_rate = (edits / approvals) if approvals else 0.0
    return {
        "funnel": counts,
        "blocks": blocks,
        "approval_rate": approvals / max(1, counts.get("drafted", 0) + approvals),
        "edit_rate": edit_rate,
        "sends_today": store.sends_today,
        "suppressions": len(store.suppressions),
    }
