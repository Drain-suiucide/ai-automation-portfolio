from __future__ import annotations

import re
from typing import Protocol

from app.models import Draft, DraftSentence, Fact, Lead, LeadState
from app.settings import get_settings, load_yaml
from app.state_machine import transition


class LLMProvider(Protocol):
    def fill_slots(
        self, lead: Lead, facts: list[Fact]
    ) -> tuple[str, str, list[DraftSentence], str]:
        """Return subject, body, sentences, fit_rationale."""
        ...


class FakeLLM:
    """Deterministic slot filler — no network, no hallucination of unsourced facts."""

    def fill_slots(
        self, lead: Lead, facts: list[Fact]
    ) -> tuple[str, str, list[DraftSentence], str]:
        first = lead.contact_name.split()[0] if lead.contact_name else "there"
        company = lead.company
        settings = get_settings()
        sentences: list[DraftSentence] = []

        tech = next((f for f in facts if f.type == "tech_stack"), None)
        event = next((f for f in facts if f.type == "recent_event"), None)

        if tech:
            text = f"I noticed {company} {tech.value.rstrip('.')}."
            sentences.append(DraftSentence(text=text, fact_ids=[tech.id]))
        if event:
            text = f"Also saw that you {event.value.replace('Recently:', '').strip()}."
            sentences.append(DraftSentence(text=text, fact_ids=[event.id]))

        personalized = " ".join(s.text for s in sentences)
        body_parts = [
            f"Hi {first},",
            personalized or f"I have been following {company}'s growth in your space.",
            "Would a short call next week to compare notes on outbound ops be useful?",
            f"— {settings.sender_name}",
            "Unsubscribe: {{unsubscribe_url}}",
        ]
        body = "\n\n".join(p for p in body_parts if p)
        subject = f"Ideas for {company}'s outbound flow"
        rationale = (
            f"Tier fit based on industry={lead.industry}, size={lead.size_hint}, "
            f"score={lead.icp_score}. Facts used: {[f.id for f in facts[:3]]}."
        )
        return subject, body, sentences, rationale


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def build_draft(lead: Lead, llm: LLMProvider, store: object | None = None) -> Lead:
    settings = get_settings()
    limits = load_yaml("send_limits.yml")
    max_words = int(limits.get("max_words", 120))

    subject, body, sentences, rationale = llm.fill_slots(lead, lead.facts)
    if word_count(body) > max_words:
        body = " ".join(body.split()[:max_words]) + "…"

    draft = Draft(
        lead_id=lead.id,
        tier=lead.tier or "C",
        icp_score=lead.icp_score,
        score_breakdown=list(lead.score_breakdown),
        subject=subject,
        body=body,
        sentences=sentences,
        fit_rationale=rationale,
        original_body=body,
        requires_approval=True,
    )
    draft.recompute_hash(lead.email)
    lead.draft = draft
    transition(lead, LeadState.DRAFTED)
    if store is not None:
        store.append_audit("drafted", lead.id, hash=draft.content_hash)  # type: ignore[attr-defined]
    _ = settings  # used for sender in fake llm
    return lead


def neutral_draft(lead: Lead) -> Draft:
    settings = get_settings()
    first = lead.contact_name.split()[0] if lead.contact_name else "there"
    body = (
        f"Hi {first},\n\n"
        f"I work with teams similar to {lead.company} on outbound operations. "
        f"Would a brief call next week be useful?\n\n"
        f"— {settings.sender_name}\n\n"
        "Unsubscribe: {{unsubscribe_url}}"
    )
    draft = Draft(
        lead_id=lead.id,
        tier=lead.tier or "C",
        icp_score=lead.icp_score,
        score_breakdown=list(lead.score_breakdown),
        subject=f"Quick note for {lead.company}",
        body=body,
        sentences=[],
        grounding="neutral",
        fit_rationale="Neutral template — enrichment unavailable or grounding failed.",
        original_body=body,
        requires_approval=True,
    )
    draft.recompute_hash(lead.email)
    return draft
