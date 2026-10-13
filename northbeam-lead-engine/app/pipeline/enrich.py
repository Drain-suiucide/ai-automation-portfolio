from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.models import Fact, Lead, LeadState, new_id, utcnow
from app.settings import get_settings
from app.state_machine import transition

INJECTION_PATTERNS = (
    r"ignore (all )?(previous|prior)?\s*instructions",
    r"offer\s+\d+%\s+discount",
    r"you are now",
    r"system prompt",
    r"disregard.*rules",
)

USER_AGENT = "NorthbeamLeadEngineBot/0.1 (+https://northbeam.example/bot)"


class EnrichmentProvider:
    def enrich(self, lead: Lead) -> list[Fact]:
        raise NotImplementedError


class FakeWebEnrichment(EnrichmentProvider):
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.fakeweb_base_url).rstrip("/")
        self._client = client or httpx.Client(timeout=5.0, headers={"User-Agent": USER_AGENT})
        self._cache: dict[str, str] = {}
        self._last_fetch = 0.0
        self.min_interval = 0.05

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_fetch
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_fetch = time.monotonic()

    def _robots_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        try:
            self._rate_limit()
            resp = self._client.get(robots_url)
            if resp.status_code >= 400:
                return True
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(USER_AGENT, url)
        except httpx.HTTPError:
            return False

    def _fetch(self, url: str) -> str | None:
        if not self._robots_allowed(url):
            return None
        digest_key = hashlib.sha256(url.encode()).hexdigest()
        if digest_key in self._cache:
            return self._cache[digest_key]
        self._rate_limit()
        try:
            resp = self._client.get(url)
            if resp.status_code != 200:
                return None
            body = resp.text
            self._cache[digest_key] = body
            return body
        except httpx.HTTPError:
            return None

    def _detect_injection(self, text: str) -> bool:
        lower = text.lower()
        return any(re.search(p, lower) for p in INJECTION_PATTERNS)

    def _extract_facts(self, lead: Lead, url: str, html: str) -> list[Fact]:
        facts: list[Fact] = []
        # Treat page text as data only — never as instructions.
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        patterns: list[tuple[str, str, str]] = [
            ("industry", r"Industry:\s*([A-Za-z]+)", "industry"),
            ("size_hint", r"Employees:\s*(\d+)", "size"),
            ("products", r"Products?:\s*([A-Za-z0-9 ,\-]+)", "products"),
            (
                "tech_stack",
                r"(?:runs on|powered by|uses)\s+"
                r"([A-Za-z0-9][A-Za-z0-9 .+]{0,40}?)"
                r"(?:\.|$|\s+Recently)",
                "tech_stack",
            ),
            ("recent_event", r"Recently:\s*([^.]+)", "recent_event"),
        ]
        for ftype, pattern, _ in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if not m:
                continue
            value = m.group(0).strip()
            snippet = text[max(0, m.start() - 20) : m.end() + 40].strip()
            facts.append(
                Fact(
                    id=new_id("fact"),
                    type=ftype,
                    value=value,
                    source_url=url,
                    snippet=snippet,
                    fetched_at=utcnow(),
                )
            )
            if ftype == "industry":
                lead.industry = m.group(1).strip().lower()
            if ftype == "size_hint":
                try:
                    lead.size_hint = int(m.group(1))
                except ValueError:
                    pass
        return facts

    def enrich(self, lead: Lead) -> list[Fact]:
        slug = lead.canonical_domain.split(".")[0] if lead.canonical_domain else "unknown"
        url = urljoin(self.base_url + "/", f"{slug}/about.html")
        html = self._fetch(url)
        if html is None:
            return []
        if self._detect_injection(html):
            lead.security_flag = True
            # Still extract safe structured fields but ignore instruction-like content.
        return self._extract_facts(lead, url, html)


class StaticEnrichment(EnrichmentProvider):
    """Offline enrichment for tests without nginx."""

    def __init__(self, pages: Mapping[str, str] | None = None) -> None:
        self.pages = dict(pages or {})

    def enrich(self, lead: Lead) -> list[Fact]:
        slug = lead.canonical_domain.split(".")[0]
        html = self.pages.get(slug, "")
        if not html:
            return []
        provider = FakeWebEnrichment(base_url="http://fakeweb")
        url = f"http://fakeweb/{slug}/about"
        if provider._detect_injection(html):  # noqa: SLF001
            lead.security_flag = True
        return provider._extract_facts(lead, url, html)  # noqa: SLF001


def enrich_lead(lead: Lead, provider: EnrichmentProvider, store: Any = None) -> Lead:
    facts = provider.enrich(lead)
    lead.facts = facts
    if not facts:
        transition(lead, LeadState.NEEDS_DATA)
    else:
        transition(lead, LeadState.ENRICHED)
    if store is not None:
        store.append_audit(
            "enriched",
            lead.id,
            fact_count=len(facts),
            security_flag=lead.security_flag,
        )
    return lead
