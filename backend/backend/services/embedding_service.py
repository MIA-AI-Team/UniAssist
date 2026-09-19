# backend/services/embedding_service.py
from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.file import Embedding
from ai_tutor.parsers import extract_text_from_file
from fastapi.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError
from backend.services.access import fail

MAX_REFERENCE_CHARS = int(os.getenv("MAX_REFERENCE_CHARS", 12000))
CHUNK_SIZE = 1000
PLACEHOLDER_MODEL_VERSION = "none:text-chunk-only"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, max_total_chars: int = MAX_REFERENCE_CHARS) -> list[str]:
    text = text.strip()[:max_total_chars]
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return [c for c in chunks if c.strip()]


async def create_embeddings_for_file(
    file_id: int,
    task_id: int | None,
    file_path: str,
    db: AsyncSession,
) -> None:
    """
    Chunk an uploaded file's text and store it for later reference-text
    lookup. No real embedding vectors are generated — vector_id is a
    placeholder, not a functioning vector-DB pointer. If/when semantic
    search is needed, these rows should be backfilled by filtering on
    model_version == PLACEHOLDER_MODEL_VERSION.
    """
    try:
        raw_text = await run_in_threadpool(extract_text_from_file, file_path)
    except (ValueError, PdfReadError):
        fail("invalid_file", "The reference PDF could not be read.", 422)
    if not raw_text.strip():
        return

    chunks = chunk_text(raw_text)

    for index, chunk in enumerate(chunks):
        db.add(
            Embedding(
                file_id=file_id,
                task_id=task_id,
                chunk_index=index,
                chunk_text=chunk,
                vector_id=f"placeholder:file-{file_id}:chunk-{index}",
                model_version=PLACEHOLDER_MODEL_VERSION,
            )
        )

    await db.flush()
