

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.enums import UserRole
from backend.database import Base
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,

)
import datetime as dt


 
class User(Base):
    __tablename__ = "users"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ) 
    admin: Mapped["Admin | None"] = relationship(back_populates="user", uselist=False)
    staff: Mapped["Staff | None"] = relationship(back_populates="user", uselist=False)
    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False)
 
 
class Admin(Base):
    __tablename__ = "admins"
 
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    permission_level: Mapped[str] = mapped_column(String(50))
 
    user: Mapped["User"] = relationship(back_populates="admin")
 
 
class Staff(Base):
    __tablename__ = "staff"
 
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    staff_role: Mapped[str] = mapped_column(String(50))  # professor | teaching_assistant
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
 
    user: Mapped["User"] = relationship(back_populates="staff")
 
 
class Student(Base):
    __tablename__ = "students"
 
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    student_number: Mapped[str] = mapped_column(String(50), unique=True)
    cohort_year: Mapped[int] = mapped_column(Integer)
    major: Mapped[str] = mapped_column(String(255))
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
 
    user: Mapped["User"] = relationship(back_populates="student")
 
 