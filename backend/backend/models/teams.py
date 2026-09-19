from __future__ import annotations

from typing import TYPE_CHECKING

import datetime as dt
from sqlalchemy import ForeignKey, String, DateTime, JSON, Boolean, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.repository import Repository
    from backend.models.users import Student
    from backend.models.tasks import Task


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("created_by", "request_id", name="uq_team_create_request"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("students.user_id"))
    request_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(24), default="draft", server_default="legacy")
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    approved_roster: Mapped[dict | None] = mapped_column(JSON)
    locked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped[Task] = relationship("Task")
    members: Mapped[list[TeamMember]] = relationship(back_populates="team", cascade="all, delete-orphan")
    repositories: Mapped[list[Repository]] = relationship(back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (Index("uq_active_task_membership", "task_id", "student_id", unique=True, postgresql_where=text("active")),)


    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    student_id: Mapped[int] = mapped_column( ForeignKey("students.user_id", ondelete="CASCADE"), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    accepted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    team: Mapped[Team] = relationship(back_populates="members")
    student: Mapped[Student] = relationship("Student")


class TeamInvitation(Base):
    __tablename__ = "team_invitations"
    __table_args__ = (Index("uq_pending_team_invitation", "team_id", "student_id", unique=True,
                           postgresql_where=text("status = 'pending'")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.user_id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
    responded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class TeamEvent(Base):
    __tablename__ = "team_events"
    __table_args__ = (UniqueConstraint("actor_id", "request_id", name="uq_team_event_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    request_id: Mapped[str] = mapped_column(String(36))
    request_hash: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(24))
    version: Mapped[int] = mapped_column()
    roster: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
