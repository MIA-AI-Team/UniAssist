from __future__ import annotations
 
import datetime as dt
from typing import TYPE_CHECKING
from backend.database import Base

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from backend.models.enums import SubmissionStatus

if TYPE_CHECKING:
    from backend.models.tasks import Task
    from backend.models.rubric import Rubric
    from backend.models.repository import CodeReview
    from backend.models.file import File
    from backend.models.chat import ChatSession
class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", "attempt_number", name="uq_submission_attempt"),
    )
 
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.user_id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id"))
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)
    submitted_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        nullable=False,
    )
    ai_suggested_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.pending)
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("staff.user_id"), nullable=True)
    confirmed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
 
    task: Mapped["Task"] = relationship(back_populates="submissions")
    rubric: Mapped["Rubric"] = relationship(back_populates="submissions")
    files: Mapped[list["File"]] = relationship(back_populates="submission")
    code_reviews: Mapped[list["CodeReview"]] = relationship(back_populates="submission")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="submission")


