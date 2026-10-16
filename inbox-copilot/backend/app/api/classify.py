from fastapi import APIRouter, HTTPException

from app.schemas.classification import ClassifyRequest, ClassifyResponse
from app.services.classifier import classify_email
from app.services.llm_client import LLMError

router = APIRouter(prefix="/classify", tags=["classify"])


@router.post("", response_model=ClassifyResponse)
def classify(payload: ClassifyRequest) -> ClassifyResponse:
    try:
        result, meta = classify_email(
            subject=payload.subject,
            body=payload.body,
            from_address=payload.from_address,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ClassifyResponse(classification=result, meta=meta)