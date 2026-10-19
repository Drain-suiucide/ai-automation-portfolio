from app.prompts.prioritizer import SYSTEM_PROMPT, build_user_prompt
from app.schemas.classification import LLMMeta
from app.schemas.prioritization import PriorityResult
from app.services.llm_client import structured_completion


def prioritize_email(
    *,
    subject: str | None,
    body: str,
    from_address: str | None = None,
    category: str | None = None,
    sentiment: str | None = None,
    urgency: str | None = None,
) -> tuple[PriorityResult, LLMMeta]:
    user_prompt = build_user_prompt(
        subject=subject,
        body=body,
        from_address=from_address,
        category=category,
        sentiment=sentiment,
        urgency=urgency,
    )
    parsed, meta_dict = structured_completion(
        schema=PriorityResult,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=800,
    )
    return parsed, LLMMeta(**meta_dict)