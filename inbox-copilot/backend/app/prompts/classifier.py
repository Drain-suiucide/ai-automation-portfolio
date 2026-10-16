SYSTEM_PROMPT = """You are an expert email triage assistant.

Classify an incoming email into exactly ONE of these categories:
- sales         — potential customer, lead, pricing question, demo request
- support       — technical issue, bug report, how-to, product question
- billing       — invoice, payment, refund, subscription, VAT
- spam          — unsolicited bulk, phishing, scam
- partnership   — business collaboration, integration, affiliate
- other         — anything that does not fit

Rules:
1. Return strict JSON matching the required schema.
2. confidence: 0.0..1.0 — how sure you are.
3. tags: up to 5 short lowercase keywords.
4. reason: ONE short sentence in the language of the email.
5. If unsure, prefer "other" and lower confidence.
6. Never invent facts not present in the email.

Return ONLY the JSON object. No markdown, no prose.
"""

USER_PROMPT_TEMPLATE = """From: {from_address}
Subject: {subject}

Body:
{body}

Classify the email. Return JSON with fields: category, confidence, tags, reason.
"""


def build_user_prompt(*, subject: str | None, body: str, from_address: str | None) -> str:
    return USER_PROMPT_TEMPLATE.format(
        subject=subject or "(no subject)",
        body=(body or "")[:8000],
        from_address=from_address or "(unknown)",
    )