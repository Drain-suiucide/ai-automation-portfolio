SYSTEM_PROMPT = """You are an email triage prioritizer.

Assign a priority:
- P0 — critical: outage, security incident, angry VIP, legal threat, hard deadline today
- P1 — high: important customer, deadline within 3 days, significant amount, blocker
- P2 — normal: routine request requiring a reply
- P3 — low: informational, FYI, no action needed

Rules:
1. Return ONLY strict JSON with fields: priority, score, factors, reason.
2. score: 0.0..1.0 — confidence-weighted severity.
3. factors: up to 5 short explanations.
4. reason: ONE sentence.
5. Do not invent facts.

Return ONLY the JSON object.
"""

USER_PROMPT_TEMPLATE = """From: {from_address}
Subject: {subject}
Category: {category}
Sentiment: {sentiment}
Urgency: {urgency}

Body:
{body}

Assign priority. Return JSON with fields: priority, score, factors, reason.
"""


def build_user_prompt(
    *,
    subject: str | None,
    body: str,
    from_address: str | None,
    category: str | None,
    sentiment: str | None,
    urgency: str | None,
) -> str:
    return USER_PROMPT_TEMPLATE.format(
        subject=subject or "(no subject)",
        body=(body or "")[:8000],
        from_address=from_address or "(unknown)",
        category=category or "null",
        sentiment=sentiment or "null",
        urgency=urgency or "null",
    )