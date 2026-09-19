from __future__ import annotations

from sqlalchemy import select , update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.file import Embedding
from backend.models.tasks import Task


async def get_reference_text(
    task_id: int,
    db: AsyncSession,
) -> str:
    result = await db.execute(
        select(Embedding)
        .where(Embedding.file_id == select(Task.reference_file_id).where(Task.id == task_id).scalar_subquery())
        .order_by(Embedding.chunk_index.asc())
    )

    chunks = result.scalars().all()

    if not chunks:
        return ""

    return "\n\n".join(
        chunk.chunk_text
        for chunk in chunks
    )

async def link_embeddings_to_task(
    file_id: int,
    task_id: int,
    db: AsyncSession,
) -> None:
    print("link_embeddings_to_task called with file_id:", file_id, "task_id:", task_id)
    await db.execute(
        update(Embedding)
        .where(Embedding.file_id == file_id)
        .values(task_id=task_id)
    )
    await db.flush()
