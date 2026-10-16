import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Thread(Base, TimestampMixin):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True
    )
    external_thread_id: Mapped[str] = mapped_column(String(512), index=True)
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    mailbox: Mapped["Mailbox"] = relationship(back_populates="threads")  # noqa: F821
    emails: Mapped[list["Email"]] = relationship(  # noqa: F821
        back_populates="thread", cascade="all, delete-orphan"
    )