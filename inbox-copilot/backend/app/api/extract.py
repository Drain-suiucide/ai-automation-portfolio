from fastapi import APIRouter, HTTPException

from app.schemas.extraction import ExtractRequest, ExtractResponse
from app.services.extractor import extract_entities
from app.services.llm_client import LLMError

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("", response_model=ExtractResponse)
def extract(payload: ExtractRequest) -> ExtractResponse:
    try:
        entities, meta = extract_entities(
            subject=payload.subject,
            body=payload.body,
            from_address=payload.from_address,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ExtractResponse(entities=entities, meta=meta)