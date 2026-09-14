from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
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

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
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