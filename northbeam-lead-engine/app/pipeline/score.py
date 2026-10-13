from __future__ import annotations

from typing import Any

from app.models import Lead, LeadState, ScoreBreakdownItem
from app.settings import load_yaml
from app.state_machine import transition


def _load_icp() -> dict[str, Any]:
    return load_yaml("icp.yml")


def score_lead(lead: Lead, store: Any = None) -> Lead:
    """Deterministic ICP scoring. LLM cannot change the numeric score (INV-6)."""
    cfg = _load_icp()
    breakdown: list[ScoreBreakdownItem] = []
    total = 0

    # Stop-list short-circuit
    stop_domains = {d.lower() for d in cfg.get("stop_list", {}).get("domains", [])}
    stop_companies = {c.lower() for c in cfg.get("stop_list", {}).get("companies", [])}
    if lead.canonical_domain in stop_domains or lead.canonical_company in stop_companies:
        lead.icp_score = 0
        lead.tier = "C"
        lead.score_breakdown = [ScoreBreakdownItem(rule="stop_list", points=0)]
        lead.archive_reason = "stop_list"
        if lead.state != LeadState.SCORED:
            transition(lead, LeadState.SCORED)
        transition(lead, LeadState.ARCHIVED)
        if store is not None:
            store.append_audit("scored", lead.id, score=0, tier="C", reason="stop_list")
        return lead

    industry = (lead.industry or "other").lower()
    industries = cfg.get("industries", {})
    pts = int(industries.get(industry, industries.get("other", 5)))
    breakdown.append(ScoreBreakdownItem(rule=f"industry:{industry}", points=pts))
    total += pts

    size = lead.size_hint
    if size is not None:
        for band in cfg.get("size_bands", []):
            if int(band["min"]) <= size <= int(band["max"]):
                bpts = int(band["points"])
                breakdown.append(
                    ScoreBreakdownItem(rule=f"size:{band['name']}", points=bpts)
                )
                total += bpts
                break

    geo = cfg.get("geography", {})
    gpts = int(geo.get(lead.country.upper(), geo.get("default", 4)))
    breakdown.append(ScoreBreakdownItem(rule=f"geo:{lead.country.upper()}", points=gpts))
    total += gpts

    tech_bonus = cfg.get("tech_bonus", {})
    for fact in lead.facts:
        if fact.type != "tech_stack":
            continue
        for tech, bonus in tech_bonus.items():
            if tech.lower() in fact.value.lower():
                breakdown.append(ScoreBreakdownItem(rule=f"tech:{tech}", points=int(bonus)))
                total += int(bonus)

    # Injection pages must not alter scoring beyond extracted structured facts.
    if lead.security_flag:
        breakdown.append(ScoreBreakdownItem(rule="security_flag_ignored_instructions", points=0))

    total = max(0, min(100, total))
    thresholds = cfg.get("tier_thresholds", {"A": 70, "B": 45, "C": 0})
    if total >= int(thresholds["A"]):
        tier = "A"
    elif total >= int(thresholds["B"]):
        tier = "B"
    else:
        tier = "C"

    lead.icp_score = total
    lead.tier = tier  # type: ignore[assignment]
    lead.score_breakdown = breakdown

    # Always land on scored first, then route by tier (FR-6 / FR-13).
    if lead.state != LeadState.SCORED:
        transition(lead, LeadState.SCORED)

    if tier == "B":
        lead.archive_reason = None
        transition(lead, LeadState.NURTURE)
    elif tier == "C":
        lead.archive_reason = lead.archive_reason or "low_icp"
        transition(lead, LeadState.ARCHIVED)

    if store is not None:
        store.append_audit("scored", lead.id, score=total, tier=tier, breakdown=breakdown)
    return lead
