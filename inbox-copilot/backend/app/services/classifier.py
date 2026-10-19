from app.prompts.classifier import SYSTEM_PROMPT, build_user_prompt
from app.schemas.classification import ClassificationResult, LLMMeta
from app.services.llm_client import structured_completion


def classify_email(
    *,
    subject: str | None,
    body: str,
    from_address: str | None = None,
) -> tuple[ClassificationResult, LLMMeta]:
    user_prompt = build_user_prompt(
        subject=subject, body=body, from_address=from_address
    )
    parsed, meta_dict = structured_completion(
        schema=ClassificationResult,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=800,
    )
    return parsed, LLMMeta(**meta_dict)