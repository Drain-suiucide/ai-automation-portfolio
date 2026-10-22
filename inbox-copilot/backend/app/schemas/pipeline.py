from pydantic import BaseModel

from app.schemas.classification import ClassificationResult, LLMMeta
from app.schemas.extraction import ExtractedEntities
from app.schemas.prioritization import PriorityResult


class ProcessRequest(BaseModel):
    external_id: str | None = None
    subject: str | None = None
    body: str
    from_address: str | None = None


class ProcessResponse(BaseModel):
    email_id: str
    classification: ClassificationResult
    extraction: ExtractedEntities
    priority: PriorityResult
    meta: "ProcessMeta"


class ProcessMeta(BaseModel):
    classification: LLMMeta
    extraction: LLMMeta
    priority: LLMMeta


ProcessResponse.model_rebuild()