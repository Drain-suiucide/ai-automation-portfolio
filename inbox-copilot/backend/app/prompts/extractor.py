SYSTEM_PROMPT = """You are an information extraction engine for business emails.

Extract structured fields from the email. Rules:
1. Return ONLY strict JSON matching the schema. No prose, no markdown.
2. Missing fields → null. Do not guess.
3. `amount` — number only (no currency symbols). `currency` — ISO 4217 code.
4. `deadline` — ISO 8601 (YYYY-MM-DD) if a specific date is present, else null.
5. `sentiment`: positive | neutral | negative | angry.
6. `urgency`: low | normal | high | critical.
7. `language`: ISO 639-1 code.
8. `requested_action`: short imperative phrase.

Return ONLY the JSON object.
"""

USER_PROMPT_TEMPLATE = """From: {from_address}
Subject: {subject}

Body:
{body}

Extract entities. Return JSON with all schema fields.
"""


def build_user_prompt(*, subject: str | None, body: str, from_address: str | None) -> str:
    return USER_PROMPT_TEMPLATE.format(
        subject=subject or "(no subject)",
        body=(body or "")[:8000],
        from_address=from_address or "(unknown)",
    )