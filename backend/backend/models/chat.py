from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.models.enums import SenderType

if TYPE_CHECKING:
    from backend.models.repository import CodeReview
    from backend.models.file import Embedding
    from backend.models.submissions import Submission
    from backend.models.tasks import Task
    from backend.models.users import User


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (UniqueConstraint("user_id", "request_id", name="uq_chat_session_request"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    language: Mapped[str] = mapped_column(String(2), default="en", server_default="en")
    context_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    user: Mapped[User] = relationship("User")
    task: Mapped[Task | None] = relationship("Task")
    submission: Mapped[Submission | None] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by=lambda: ChatMessage.created_at)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    sources: Mapped[list[ChatMessageSource]] = relationship(back_populates="message", cascade="all, delete-orphan")


class ChatMessageSource(Base):
    __tablename__ = "chat_message_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    embedding_id: Mapped[int | None] = mapped_column(ForeignKey("embeddings.id", ondelete="SET NULL"), nullable=True)
    code_review_id: Mapped[int | None] = mapped_column(ForeignKey("code_reviews.id", ondelete="SET NULL"), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)

    message: Mapped[ChatMessage] = relationship(back_populates="sources")
    embedding: Mapped[Embedding | None] = relationship("Embedding")
    code_review: Mapped[CodeReview | None] = relationship("CodeReview")


class ChatTurn(Base):
    """Durable idempotency and lease state; message content lives in chat_messages."""
    __tablename__ = "chat_turns"
    __table_args__ = (UniqueConstraint("session_id", "request_id", name="uq_chat_turn_request"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    user_message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"))
    assistant_message_id: Mapped[int | None] = mapped_column(ForeignKey("chat_messages.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempt_count: Mapped[int] = mapped_column(default=0)
    generation: Mapped[str] = mapped_column(String(36))
    lease_until: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    is_mock: Mapped[bool | None] = mapped_column()
    context_info: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ai_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ChatShare(Base):
    __tablename__ = "chat_shares"
    __table_args__ = (UniqueConstraint("session_id", "request_id", name="uq_chat_share_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("staff.user_id"), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    through_turn_id: Mapped[int] = mapped_column()
    snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class TaskTutorSettings(Base):
    __tablename__ = "task_tutor_settings"
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    lab_mode: Mapped[str] = mapped_column(String(16), default="experiment")
    updated_by: Mapped[int] = mapped_column(ForeignKey("staff.user_id"))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
