"""Content-free audit and AI operation records. No academic content or credentials."""
import datetime as dt
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50))
    target_type: Mapped[str] = mapped_column(String(30))
    target_id: Mapped[int] = mapped_column(Integer)
    fields: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIOperation(Base):
    __tablename__ = "ai_operations"
    id: Mapped[int] = mapped_column(primary_key=True)
    operation: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(30))
    outcome: Mapped[str] = mapped_column(String(20))
    latency_ms: Mapped[float] = mapped_column(Float)
    is_mock: Mapped[bool | None] = mapped_column(Boolean)
    truncated: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
