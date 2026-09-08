"""
DB queries for authentication.
    - register_user()  — create USERS row + role extension row
    - login_user()     — verify credentials, return token
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password, verify_password, create_access_token
from backend.models.users import User, Admin, Staff, Student
from backend.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse


# TODO consider the workflow for handling the student numbers


async def register_user(data: RegisterRequest, db: AsyncSession) -> RegisterResponse:
    """
    Create a USERS row and the matching role extension row.

    Raises:
        HTTPException 400 — email already registered
        HTTPException 422 — missing required fields for the given role
    """

    # 1. Check email not already taken
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered.")

    # 2. Validate role
    allowed_roles = {"admin", "professor", "teaching_assistant", "student"}
    if data.role not in allowed_roles:
        raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of: {allowed_roles}")

    # 3. Create USERS row
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()  # get user.id without committing yet

    # 4. Create role extension row
    if data.role == "student":
        _validate_fields( # Validate required fields for students
            required={"student_number": data.student_number, "cohort_year": data.cohort_year, "major": data.major},
            role="student",
        )
        db.add(Student(
            user_id=user.id,
            student_number=data.student_number,
            cohort_year=data.cohort_year,
            major=data.major,
            github_username=data.github_username,
        ))

    elif data.role in ("professor", "teaching_assistant"):
        _validate_fields(
            required={"staff_role": data.staff_role, "department": data.department},
            role=data.role,
        )
        db.add(Staff(
            user_id=user.id,
            staff_role=data.staff_role,
            department=data.department,
        ))

    elif data.role == "admin":
        db.add(Admin(
            user_id=user.id,
            permission_level="standard",
        ))

    # 5. Commit everything together
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )




async def login_user(data: LoginRequest, db: AsyncSession) -> LoginResponse:
    """
    Verify email + password, return a signed JWT.

    Raises:
        HTTPException 401 — email not found or wrong password
    """

    # 1. Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user: User | None = result.scalar_one_or_none()

    # 2. Verify password — same error message for both cases to avoid user enumeration
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # 3. Generate token
    token = create_access_token(user_id=user.id, role=user.role)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_fields(required: dict, role: str) -> None:
    """Raise 422 if any required field for a role is missing."""
    missing = [field for field, value in required.items() if not value]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields for role '{role}': {missing}",
        )



