"""
Authentication endpoints:
    POST /auth/register  — create account
    POST /auth/login     — get JWT token
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from backend.services.auth_service import register_user, login_user
from backend.core.dependencies import get_current_user
from backend.schemas.auth import IdentityResponse
from backend.models.users import User
from backend.schemas.accounts import ProfileUpdate
from backend.services.account_service import identity, update_account

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=IdentityResponse)
async def me(user: User = Depends(get_current_user)):
    return identity(user)


@router.patch("/me", response_model=IdentityResponse)
async def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return identity(await update_account(user.id, body, user, db))


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    return await register_user(data, db)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    return await login_user(data, db)
