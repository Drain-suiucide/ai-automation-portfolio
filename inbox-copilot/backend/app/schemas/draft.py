from pydantic import BaseModel, Field

from app.schemas.classification import LLMMeta


class DraftResult(BaseModel):
    subject: str | None = Field(None, description="Suggested reply subject (usually Re: ...)")
    body_text: str = Field(description="Plain-text body")
    tone: str = Field(default="professional", description="formal|friendly|professional")
    language: str = Field(default="en", description="ISO 639-1")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    warnings: list[str] = Field(default_factory=list)
    cited_kb: list[str] = Field(default_factory=list)


class DraftResponse(BaseModel):
    draft_id: str
    email_id: str
    status: str
    subject: str | None
    body_text: str
    tone: str | None
    language: str | None
    confidence: float
    warnings: list[str]
    cited_kb: list[str]
    meta: LLMMeta


class DraftRequest(BaseModel):
    tone: str | None = Field(
        None,
        description="Optional override: formal|friendly|professional",
    )
    instructions: str | None = Field(
        None,
        description="Optional extra instructions from human",
    )