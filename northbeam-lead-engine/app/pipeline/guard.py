from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.db import Store
from app.models import Lead
from app.settings import load_yaml


def _role_blocked(email: str, prefixes: list[str]) -> bool:
    local = email.split("@")[0].lower() + "@"
    return any(local.startswith(p.lower()) for p in prefixes)


def _quiet_hours(now: datetime, tz_name: str, start: int, end: int) -> bool:
    if tz_name.upper() in {"UTC", "GMT", ""}:
        local = now.astimezone(UTC)
    else:
        try:
            tz = ZoneInfo(tz_name)
            local = now.astimezone(tz)
        except Exception:
            local = now.astimezone(UTC)
    hour = local.hour
    if start > end:
        return hour >= start or hour < end
    return start <= hour < end


def check_send_guards(lead: Lead, store: Store, now: datetime | None = None) -> str | None:
    """Re-evaluate all guards at send time (INV-1,2,3,7)."""
    now = now or datetime.now(UTC)
    limits = load_yaml("send_limits.yml")
    policy = load_yaml("country_policy.yml").get("country_policy", {})

    if lead.draft is None:
        return "approval_missing"
    draft = lead.draft

    email = lead.canonical_email or lead.email
    domain = lead.canonical_domain or lead.domain

    if store.is_suppressed(email, domain):
        return "suppressed"

    country = lead.country.upper()
    rule = policy.get(country, policy.get("default", "allow_with_opt_out"))
    if rule == "block":
        return "country_policy"
    if rule == "consent_required" and lead.lawful_basis.value != "consent":
        return "country_policy"

    role_prefixes = list(limits.get("role_addresses", []))
    if _role_blocked(email, role_prefixes):
        return "role_address"

    daily_cap = int(limits.get("daily_cap", 50))
    if store.sends_today >= daily_cap:
        return "daily_cap"

    domain_cap = int(limits.get("domain_cap", 3))
    if store.domain_sends.get(domain, 0) >= domain_cap:
        return "domain_cap"

    quiet = limits.get("quiet_hours", {})
    if _quiet_hours(now, lead.timezone, int(quiet.get("start", 21)), int(quiet.get("end", 8))):
        return "quiet_hours"

    days = int(limits.get("recently_contacted_days", 30))
    last = store.contacted_at.get(email)
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < timedelta(days=days):
            return "recently_contacted"

    if draft.requires_approval and not draft.approved_hash:
        return "approval_missing"

    current_hash = draft.recompute_hash(email)
    if draft.approved_hash and draft.approved_hash != current_hash:
        return "approval_hash_mismatch"

    if "{{unsubscribe_url}}" not in draft.body and "unsubscribe" not in draft.body.lower():
        return "missing_unsubscribe"

    if draft.grounding == "failed":
        return "grounding_failed"

    # Personalized sentences must cite valid facts (INV-4)
    fact_ids = {f.id for f in lead.facts}
    for sentence in draft.sentences:
        if not sentence.fact_ids or any(fid not in fact_ids for fid in sentence.fact_ids):
            return "grounding_failed"

    return None


def guard_detail(reason: str) -> dict[str, Any]:
    return {"reason": reason, "checked_at": datetime.now(UTC).isoformat()}
