
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, description="Plain-text password — hashed before storage")
    role: str = Field(description="admin | professor | teaching_assistant | student")

    # Student-only fields
    student_number: Optional[str] = Field(default=None, description="Required if role=student")
    cohort_year: Optional[int] = Field(default=None, description="Required if role=student")
    major: Optional[str] = Field(default=None, description="Required if role=student")
    github_username: Optional[str] = Field(default=None)

    # Staff-only fields
    staff_role: Optional[str] = Field(default=None, description="professor | teaching_assistant — required if role=professor or teaching_assistant")
    department: Optional[str] = Field(default=None, description="Required if role=professor or teaching_assistant")


class RegisterResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    message: str = "Account created successfully."


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    name: str


# ---------------------------------------------------------------------------
# Token payload (used internally by dependencies.py)
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    sub: str        # user_id as string
    role: str