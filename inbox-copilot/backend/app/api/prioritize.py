from fastapi import APIRouter, HTTPException

from app.schemas.prioritization import PrioritizeRequest, PrioritizeResponse
from app.services.llm_client import LLMError
from app.services.prioritizer import prioritize_email

router = APIRouter(prefix="/prioritize", tags=["prioritize"])


@router.post("", response_model=PrioritizeResponse)
def prioritize(payload: PrioritizeRequest) -> PrioritizeResponse:
    try:
        result, meta = prioritize_email(
            subject=payload.subject,
            body=payload.body,
            from_address=payload.from_address,
            category=payload.category,
            sentiment=payload.sentiment,
            urgency=payload.urgency,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return PrioritizeResponse(priority=result, meta=meta)