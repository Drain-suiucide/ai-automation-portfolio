import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import DraftStatus


class Draft(Base, TimestampMixin):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[DraftStatus] = mapped_column(
        SAEnum(DraftStatus, name="draft_status"),
        default=DraftStatus.draft,
        index=True,
    )

    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    body_text: Mapped[str] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    cited_kb: Mapped[list] = mapped_column(JSONB, default=list)

    # метаданные LLM
    model: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(default=0)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1")

    email: Mapped["Email"] = relationship(back_populates="drafts")  # noqa: F821