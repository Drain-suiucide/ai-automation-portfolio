from app.prompts.extractor import SYSTEM_PROMPT, build_user_prompt
from app.schemas.classification import LLMMeta
from app.schemas.extraction import ExtractedEntities
from app.services.llm_client import structured_completion


def extract_entities(
    *,
    subject: str | None,
    body: str,
    from_address: str | None = None,
) -> tuple[ExtractedEntities, LLMMeta]:
    user_prompt = build_user_prompt(subject=subject, body=body, from_address=from_address)
    parsed, meta_dict = structured_completion(
        schema=ExtractedEntities,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=1500,
    )
    return parsed, LLMMeta(**meta_dict)