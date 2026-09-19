from __future__ import annotations
 
import datetime as dt
from backend.models.enums import ReviewType, Severity
from typing import TYPE_CHECKING
from backend.database import Base

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    String, JSON, Boolean, BigInteger, LargeBinary, UniqueConstraint, Index, text
)
from sqlalchemy.orm import  Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.models.submissions import Submission
    from backend.models.teams import Team
    
class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("created_by","request_id",name="uq_repository_create_request"),
        Index("uq_active_team_repository","team_id",unique=True,postgresql_where=text("status='approved'")))
 
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    repo_url: Mapped[str] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(50), default="github")
    status: Mapped[str] = mapped_column(String(24),default="pending",server_default="legacy")
    version: Mapped[int] = mapped_column(default=1,server_default="1")
    full_name: Mapped[str | None] = mapped_column(String(150))
    github_id: Mapped[int | None] = mapped_column(BigInteger)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    request_id: Mapped[str | None] = mapped_column(String(36))
    approved_team_version: Mapped[int | None] = mapped_column()
    last_synced_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    sync_error: Mapped[str | None] = mapped_column(String(40))
    partial_history: Mapped[bool] = mapped_column(Boolean,default=True,server_default="true")
    is_fixture: Mapped[bool] = mapped_column(Boolean,default=False,server_default="false")
 
    team: Mapped["Team"] = relationship(back_populates="repositories")
    commits: Mapped[list["Commit"]] = relationship(back_populates="repository", passive_deletes=True)
 
 
class Commit(Base):
    __tablename__ = "commits"
    __table_args__ = (UniqueConstraint("repository_id","commit_hash",name="uq_repository_commit"),)
 
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.user_id"), nullable=True)
    commit_hash: Mapped[str] = mapped_column(String(64))
    author_name: Mapped[str] = mapped_column(String(255))
    author_github_username: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    committed_at: Mapped[dt.datetime] = mapped_column(DateTime)
    attributed_by: Mapped[int | None] = mapped_column(ForeignKey("staff.user_id"))
    attributed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
 
    repository: Mapped["Repository"] = relationship(back_populates="commits")
 
 
class RepositoryEvent(Base):
    __tablename__ = "repository_events"
    __table_args__ = (UniqueConstraint("actor_id","request_id",name="uq_repository_event_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id",ondelete="CASCADE"),index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    request_id: Mapped[str] = mapped_column(String(36))
    request_hash: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(24))
    version: Mapped[int] = mapped_column()
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),default=lambda:dt.datetime.now(dt.timezone.utc))


class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"
    __table_args__ = (UniqueConstraint("owner_id","request_id",name="uq_repository_snapshot_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id",ondelete="CASCADE"),index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("students.user_id"))
    request_id: Mapped[str] = mapped_column(String(36))
    commit_sha: Mapped[str] = mapped_column(String(40))
    archive: Mapped[bytes] = mapped_column(LargeBinary,deferred=True)
    provenance: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),default=lambda:dt.datetime.now(dt.timezone.utc))


class CodeReview(Base):
    __tablename__ = "code_reviews"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    commit_id: Mapped[int | None] = mapped_column(ForeignKey("commits.id", ondelete="CASCADE"), nullable=True)
    review_type: Mapped[ReviewType] = mapped_column(Enum(ReviewType))
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    finding: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(500))
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
 
    submission: Mapped["Submission"] = relationship(back_populates="code_reviews")
