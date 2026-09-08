from __future__ import annotations

from typing import Annotated, Sequence
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import decode_access_token
from backend.database import get_db
from backend.models.users import User
from backend.schemas.auth import TokenPayload

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate JWT token from Authorization header and fetch user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract the raw JWT string from Bearer credentials
    token = credentials.credentials

    try:
        payload_dict = decode_access_token(token)
        token_data = TokenPayload(
            sub=payload_dict.get("sub", ""),
            role=payload_dict.get("role", "")
        )
        if not token_data.sub:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


def require_roles(allowed_roles: Sequence[str]):
    """Role-based authorization guard factory."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}",
            )
        return current_user

    return role_checker