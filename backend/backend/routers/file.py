"""
    POST /files/upload            — upload a reference or submission file
    GET  /files/{file_id}         — get metadata of a specific file
    GET  /files/{file_id}/download — download actual file payload
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.models.enums import UserRole
from backend.models.users import User
from backend.repository import get_file_by_id
from backend.schemas.file import FileInfoResponse, FileUploadResponse
from backend.services.file_service import save_upload
from backend.services.access import check_task_access, fail
from backend.repository.task_repository import _get_task

async def check_file_access(file_record, user, db):
    if user.role == UserRole.student:
        if file_record.purpose == "reference" and file_record.task_id:
            task = await _get_task(file_record.task_id, db)
            check_task_access(task, user)
            if task.reference_file_id != file_record.id:
                fail("file_forbidden", "Reference file is not assigned to this task.", 403)
        elif file_record.owner_id != user.id:
            fail("file_forbidden", "Access denied.", 403)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", status_code=201, response_model=FileUploadResponse)
async def upload(
    file: UploadFile = File(...),
    purpose: Literal["reference", "submission", "other"] = Form(...),
    task_id: Optional[int] = Form(None),
    submission_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file and store it in the FILES table.

    purpose=reference  → lab PDF uploaded by staff, linked to a task
    purpose=submission → student submission file
    """
    file_record = await save_upload(
        file=file,
        owner_id=current_user.id,
        purpose=purpose,
        task_id=task_id,
        submission_id=submission_id,
        db=db,
    )

    return FileUploadResponse(
        file_id=file_record.id,
        file_name=file_record.original_filename or f"file-{file_record.id}.{file_record.file_type}",
        file_type=file_record.file_type,
        purpose=file_record.purpose,
        size_bytes=os.path.getsize(file_record.storage_path),
        uploaded_at=file_record.uploaded_at,
    )


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata about an uploaded file."""
    file_record = await get_file_by_id(file_id, db)
    if file_record is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found.")

    # Students can only view files they own or files linked to their submissions
    is_student = current_user.role == UserRole.student or current_user.role == "student"
    await check_file_access(file_record, current_user, db)

    return FileInfoResponse(
        file_id=file_record.id,
        file_name=file_record.original_filename or f"file-{file_record.id}.{file_record.file_type}",
        file_type=file_record.file_type,
        purpose=file_record.purpose,
        task_id=file_record.task_id,
        submission_id=file_record.submission_id,
        size_bytes=os.path.getsize(file_record.storage_path) if os.path.isfile(file_record.storage_path) else None,
        uploaded_at=file_record.uploaded_at,
    )


@router.get("/{file_id}/download", response_class=FileResponse)
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the actual file payload.

    Students can only download their own files or reference files
    linked to tasks they have access to. Staff can download any file.
    """
    file_record = await get_file_by_id(file_id, db)
    if file_record is None:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found.")

    # Access restrictions for students
    is_student = current_user.role == UserRole.student or current_user.role == "student"
    await check_file_access(file_record, current_user, db)

    # Check file exists on disk
    if not os.path.exists(file_record.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    filename = file_record.original_filename or os.path.basename(file_record.storage_path)
    return FileResponse(
        path=file_record.storage_path,
        filename=filename,
        media_type="application/octet-stream",
    )
