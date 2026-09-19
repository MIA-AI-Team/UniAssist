"""Private immutable marking guidance and explicit aggregate teaching reports."""
import datetime as dt
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class GradingGuidance(Base):
    __tablename__ = "grading_guidance"
    __table_args__ = (
        UniqueConstraint("task_id", "version", name="uq_guidance_version"),
        UniqueConstraint("task_id", "request_id", name="uq_guidance_request"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    request_id: Mapped[str] = mapped_column(String(36))
    created_by: Mapped[int] = mapped_column(ForeignKey("staff.user_id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))


class TeachingReport(Base):
    __tablename__ = "teaching_reports"
    __table_args__ = (UniqueConstraint("task_id", "request_id", name="uq_teaching_report_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"))
    rubric_version: Mapped[int] = mapped_column()
    request_id: Mapped[str] = mapped_column(String(36))
    language: Mapped[str] = mapped_column(String(2))
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    input_snapshot: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    is_mock: Mapped[bool] = mapped_column()
    ai_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(ForeignKey("staff.user_id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
