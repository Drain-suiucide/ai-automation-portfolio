SYSTEM_PROMPT = """You are an email assistant that writes reply drafts for a customer-facing team.

You will receive:
- the original email
- classification category
- extracted entities
- (optionally) tone preference and extra instructions from the human

Write a reply draft following these rules:

1. Address the sender by their first name if known, else "Hello".
2. Be concise (3-6 short sentences). No fluff.
3. Match the requested tone: formal | friendly | professional. Default: professional.
4. For `billing`: do NOT promise refunds, waivers, or legal commitments. Say the request will be reviewed.
5. For `support`: acknowledge the issue and state the next step. Do not invent solutions.
6. For `sales` / `partnership`: thank them and say a colleague will follow up.
7. For `spam`: produce a minimal polite decline, or empty body with warning ["suspected spam — review before sending"].
8. Never invent facts, amounts, dates, or policies. Use only data given.
9. If the request is ambiguous, include one clarifying question.
10. End with a professional signature line: "Best regards," (no fake names).
11. Return strict JSON matching the schema. No markdown, no prose outside JSON.

Return ONLY the JSON object immediately.
"""


USER_PROMPT_TEMPLATE = """Original email
From: {from_address}
Subject: {subject}

Body:
{body}

Context:
- category: {category}
- contact_name: {contact_name}
- company: {company}
- invoice_id: {invoice_id}
- amount: {amount} {currency}
- deadline: {deadline}
- requested_action: {requested_action}
- sentiment: {sentiment}
- urgency: {urgency}

Tone preference: {tone}
Extra instructions: {instructions}

Write the reply draft. Return JSON with fields:
subject, body_text, tone, language, confidence, warnings, cited_kb.
"""


def build_user_prompt(
    *,
    from_address: str | None,
    subject: str | None,
    body: str,
    category: str,
    contact_name: str | None,
    company: str | None,
    invoice_id: str | None,
    amount: float | None,
    currency: str | None,
    deadline: str | None,
    requested_action: str | None,
    sentiment: str,
    urgency: str,
    tone: str | None,
    instructions: str | None,
) -> str:
    return USER_PROMPT_TEMPLATE.format(
        from_address=from_address or "(unknown)",
        subject=subject or "(no subject)",
        body=(body or "")[:6000],
        category=category,
        contact_name=contact_name or "null",
        company=company or "null",
        invoice_id=invoice_id or "null",
        amount=amount if amount is not None else "null",
        currency=currency or "",
        deadline=deadline or "null",
        requested_action=requested_action or "null",
        sentiment=sentiment,
        urgency=urgency,
        tone=tone or "professional",
        instructions=instructions or "null",
    )