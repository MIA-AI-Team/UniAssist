from __future__ import annotations

import os
import uuid

import aiofiles
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import File
from backend.repository import create_file, _get_task
from backend.services.embedding_service import create_embeddings_for_file
from backend.services.access import check_task_access, student_user, fail
from backend.models.enums import UserRole

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


async def save_upload(
    file: UploadFile,
    owner_id: int,
    purpose: str,
    db: AsyncSession,
    task_id: int | None = None,
    submission_id: int | None = None,
) -> File:
    """
    Save an uploaded file to disk and insert a FILES row.
    purpose: reference | submission | other
    Raises:
        HTTPException 400 — empty file
        HTTPException 422 — invalid purpose
    """

    allowed_purposes = {"reference", "submission", "other"}
    user = await student_user(owner_id, db)
    if purpose == "reference" and user.role not in (UserRole.professor, UserRole.teaching_assistant):
        fail("staff_only", "Reference files can only be uploaded by staff.", 403)
    if purpose == "submission" and user.role != UserRole.student:
        fail("student_only", "Submission files can only be uploaded by students.", 403)
    if submission_id is not None:
        fail("immutable_artifact", "Upload first, then attach the file by creating an attempt.", 422)
    if task_id is not None:
        check_task_access(await _get_task(task_id, db), user)

    if purpose not in allowed_purposes:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid purpose. Must be one of: {allowed_purposes}",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file has no filename.",
        )

    ext = os.path.splitext(file.filename)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    folder = os.path.join(UPLOAD_DIR, purpose)
    os.makedirs(folder, exist_ok=True)

    storage_path = os.path.join(folder, unique_name)

    contents = await file.read(25 * 1024 * 1024 + 1)
    if len(contents) > 25 * 1024 * 1024:
        fail("file_too_large", "Maximum upload size is 25 MiB.", 413)
    if purpose == "reference" and (ext != ".pdf" or not contents.startswith(b"%PDF-")):
        fail("lab_pdf_required", "Reference uploads must be PDF files.", 422)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(contents)

    file_record = File(
        owner_id=owner_id,
        task_id=task_id,
        submission_id=submission_id,
        purpose=purpose,
        file_type=ext.lstrip(".") or "unknown",
        storage_path=storage_path,
        original_filename=os.path.basename(file.filename.replace("\\", "/"))[:255],
    )

    await create_file(file_record, db)

    await db.flush()  
    if task_id and purpose == "reference":
        task = await _get_task(task_id, db)
        task.reference_file_id = file_record.id
    if purpose == "reference":
        await create_embeddings_for_file(file_id=file_record.id, task_id=task_id, file_path=storage_path, db=db)

        

    await db.commit()
    await db.refresh(file_record)

    return file_record
