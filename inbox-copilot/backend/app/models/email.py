import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import EmailDirection


class Email(Base, TimestampMixin):
    __tablename__ = "emails"
    __table_args__ = (
        Index("ix_emails_mailbox_received", "mailbox_id", "received_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), index=True
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True, nullable=True
    )
    external_message_id: Mapped[str] = mapped_column(
        String(998), unique=True, index=True
    )
    direction: Mapped[EmailDirection] = mapped_column(
        SAEnum(EmailDirection, name="email_direction"), nullable=False
    )

    from_address: Mapped[str] = mapped_column(String(320))
    from_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    to_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    cc_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    bcc_addresses: Mapped[list] = mapped_column(JSONB, default=list)

    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_headers: Mapped[dict] = mapped_column(JSONB, default=dict)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)

    thread: Mapped["Thread"] = relationship(back_populates="emails")  # noqa: F821
    attachments: Mapped[list["Attachment"]] = relationship(  # noqa: F821
        back_populates="email", cascade="all, delete-orphan"
    )
    classification: Mapped["Classification | None"] = relationship(  # noqa: F821
        back_populates="email", uselist=False, cascade="all, delete-orphan"
    )
    extraction: Mapped["Extraction | None"] = relationship(  # noqa: F821
        back_populates="email", uselist=False, cascade="all, delete-orphan"
    )
    priority: Mapped["Priority | None"] = relationship(  # noqa: F821
        back_populates="email", uselist=False, cascade="all, delete-orphan"
    )