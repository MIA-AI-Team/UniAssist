from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from backend.database import Base
from backend.models.enums import TaskType

if TYPE_CHECKING:
    from backend.models.rubric import Rubric
    from backend.models.submissions import Submission
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_cohort_year: Mapped[int] = mapped_column(nullable=False)
    target_major: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("staff.user_id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lab_details: Mapped["TaskLabDetails | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")
    assignment_details: Mapped["TaskAssignmentDetails | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")
    project_details: Mapped["TaskProjectDetails | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")
    rubrics: Mapped[list["Rubric"]] = relationship(back_populates="task")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="task")


class TaskLabDetails(Base):
    __tablename__ = "task_lab_details"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    scheduled_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference_file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="lab_details")


class TaskAssignmentDetails(Base):
    __tablename__ = "task_assignment_details"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    allowed_file_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    allow_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="assignment_details")


class TaskProjectDetails(Base):
    __tablename__ = "task_project_details"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    default_repo_provider: Mapped[str] = mapped_column(String(50), default="github", nullable=False)
    require_team: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="project_details")