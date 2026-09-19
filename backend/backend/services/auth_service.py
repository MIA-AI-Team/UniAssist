
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.models.users import Admin, Staff, Student, User
from backend.repository.user_repository import get_user_by_email, get_student_by_number
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)


async def register_user(
    data: RegisterRequest,
    db: AsyncSession,
) -> RegisterResponse:
    """
    Register a new user and create the corresponding
    role extension row.

    Raises:
        HTTPException 400 — email already registered
        HTTPException 422 — invalid role or missing role fields
    """

    existing_user = await get_user_by_email(data.email, db)

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered.",
        )

    allowed_roles = {
        "professor",
        "teaching_assistant",
        "student",
    }

    if data.role not in allowed_roles:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role. Must be one of: {allowed_roles}",
        )

    if data.role == "student":
        _validate_fields(
            required={
                "student_number": data.student_number,
                "cohort_year": data.cohort_year,
                "major": data.major,
            },
            role="student",
        )
        existing_student = await get_student_by_number( data.student_number, db, )
        if existing_student is not None:
            raise HTTPException(
                status_code=400,
                detail="Student number already registered.",
            )

    elif data.role in {"professor", "teaching_assistant"}:
        _validate_fields(
            required={
                "staff_role": data.staff_role,
                "department": data.department,
            },
            role=data.role,
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )

    db.add(user)
    await db.flush()

    if data.role == "student":
        db.add(
            Student(
                user_id=user.id,
                student_number=data.student_number,
                cohort_year=data.cohort_year,
                major=data.major,
                github_username=data.github_username,
            )
        )

    elif data.role in {"professor", "teaching_assistant"}:
        db.add(
            Staff(
                user_id=user.id,
                staff_role=data.role,
                department=data.department,
            )
        )

    elif data.role == "admin":
        db.add(
            Admin(
                user_id=user.id,
                permission_level="standard",
            )
        )

    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


async def login_user(
    data: LoginRequest,
    db: AsyncSession,
) -> LoginResponse:
    """
    Verify credentials and return a signed JWT.

    Raises:
        HTTPException 401 — invalid email or password
    """

    user = await get_user_by_email(data.email, db)

    # Use the same error for both cases to prevent
    # user enumeration.
    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"X-Error-Code": "invalid_credentials"},
        )

    #  Generate access token
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is suspended.",
                            headers={"X-Error-Code": "account_suspended"})
    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


def _validate_fields(
    required: dict,
    role: str,
) -> None:
    """
    Validate fields required by a specific role.

    Raises:
        HTTPException 422 — required field is missing
    """

    missing = [
        field
        for field, value in required.items()
        if value is None or value == ""
    ]

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields for role '{role}': {missing}",
        )
