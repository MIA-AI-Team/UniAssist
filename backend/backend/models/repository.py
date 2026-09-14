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
    String
)
from sqlalchemy.orm import  Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.models.submissions import Submission
    from backend.models.teams import Team
    
class Repository(Base):
    __tablename__ = "repositories"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    repo_url: Mapped[str] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(50), default="github")
 
    team: Mapped["Team"] = relationship(back_populates="repositories")
    commits: Mapped[list["Commit"]] = relationship(back_populates="repository")
 
 
class Commit(Base):
    __tablename__ = "commits"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.user_id"), nullable=True)
    commit_hash: Mapped[str] = mapped_column(String(64))
    author_name: Mapped[str] = mapped_column(String(255))
    author_github_username: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    committed_at: Mapped[dt.datetime] = mapped_column(DateTime)
 
    repository: Mapped["Repository"] = relationship(back_populates="commits")
 
 
class CodeReview(Base):
    __tablename__ = "code_reviews"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    commit_id: Mapped[int | None] = mapped_column(ForeignKey("commits.id"), nullable=True)
    review_type: Mapped[ReviewType] = mapped_column(Enum(ReviewType))
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    finding: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(500))
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
 
    submission: Mapped["Submission"] = relationship(back_populates="code_reviews")
 
 