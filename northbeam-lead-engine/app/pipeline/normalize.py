from __future__ import annotations

import re

COMPANY_SUFFIXES = (
    r"\b(ltd|llc|inc|gmbh|ag|plc|corp|corporation|co|company|limited|sas|bv|oy|ab)\b"
)


def normalize_domain(raw: str) -> str:
    d = raw.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0]
    d = d.removeprefix("www.")
    return d


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def normalize_company(raw: str) -> str:
    name = raw.strip().lower()
    name = re.sub(COMPANY_SUFFIXES, "", name, flags=re.IGNORECASE)
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def apply_normalization(company: str, domain: str, email: str) -> tuple[str, str, str]:
    return normalize_company(company), normalize_domain(domain), normalize_email(email)
