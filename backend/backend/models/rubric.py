from __future__ import annotations
 
import datetime as dt
from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING
 
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import  Mapped, mapped_column, relationship

from backend.database import Base
from backend.models.enums import RubricSource, RubricStatus
if TYPE_CHECKING:
    from backend.models.tasks import Task
    from backend.models.submissions import Submission

class Rubric(Base):
    __tablename__ = "rubrics"
    __table_args__ = (UniqueConstraint("task_id", "version", name="uq_rubric_task_version"),)
 
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    source: Mapped[RubricSource] = mapped_column(Enum(RubricSource))
    status: Mapped[RubricStatus] = mapped_column(Enum(RubricStatus), default=RubricStatus.pending)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("staff.user_id"), nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
    DateTime(timezone=True), 
    default=lambda: datetime.now(timezone.utc)
)
 
    task: Mapped["Task"] = relationship(back_populates="rubrics")
    criteria: Mapped[list["RubricCriteria"]] = relationship(
        back_populates="rubric", cascade="all, delete-orphan", order_by="RubricCriteria.sort_order"
    )
    submissions: Mapped[list["Submission"]] = relationship(back_populates="rubric")
 
 
class RubricCriteria(Base):
    __tablename__ = "rubric_criteria"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    max_points: Mapped[float] = mapped_column(Float)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
 
    rubric: Mapped["Rubric"] = relationship(back_populates="criteria")
