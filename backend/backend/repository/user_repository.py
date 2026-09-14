from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.users import Student, Student, User


async def get_user_by_email(
    email: str,
    db: AsyncSession,
) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email)
    )

    return result.scalar_one_or_none()


async def get_user_by_id(
    user_id: int,
    db: AsyncSession,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()


async def create_user(
    user: User,
    db: AsyncSession,
) -> User:
    db.add(user)
    await db.flush()

    return user


async def create_role_extension(
    role_model,
    db: AsyncSession,
):
    db.add(role_model)
    await db.flush()

    
async def get_student_by_number( 
        student_number: str,
          db: AsyncSession,
) -> Student | None: 
    result = await db.execute( select(Student).where( Student.student_number == student_number ) ) 
    return result.scalar_one_or_none()