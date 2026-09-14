from __future__ import annotations

from backend.models.file import File

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
async def create_file(
    file_record: File,
    db: AsyncSession,
) -> File:
    db.add(file_record)
    await db.flush()

    return file_record
async def get_file_by_id(
    file_id: int,
    db: AsyncSession,
) -> File | None:
    result = await db.execute(
        select(File).where(File.id == file_id)
    )

    return result.scalar_one_or_none()
