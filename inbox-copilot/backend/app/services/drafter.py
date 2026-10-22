from app.prompts.drafter import SYSTEM_PROMPT, build_user_prompt
from app.schemas.classification import LLMMeta
from app.schemas.draft import DraftResult
from app.services.llm_client import structured_completion


def generate_draft(
    *,
    from_address: str | None,
    subject: str | None,
    body: str,
    category: str,
    contact_name: str | None = None,
    company: str | None = None,
    invoice_id: str | None = None,
    amount: float | None = None,
    currency: str | None = None,
    deadline: str | None = None,
    requested_action: str | None = None,
    sentiment: str = "neutral",
    urgency: str = "normal",
    tone: str | None = None,
    instructions: str | None = None,
) -> tuple[DraftResult, LLMMeta]:
    user_prompt = build_user_prompt(
        from_address=from_address,
        subject=subject,
        body=body,
        category=category,
        contact_name=contact_name,
        company=company,
        invoice_id=invoice_id,
        amount=amount,
        currency=currency,
        deadline=deadline,
        requested_action=requested_action,
        sentiment=sentiment,
        urgency=urgency,
        tone=tone,
        instructions=instructions,
    )
    parsed, meta_dict = structured_completion(
        schema=DraftResult,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1500,
    )
    return parsed, LLMMeta(**meta_dict)