"""
Handles submission creation and retrieval:
    - create_submission()       — student submits work
    - get_student_submissions() — student views their own submissions for a task
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.submissions import Submission
from backend.models.tasks import Task
from backend.models.enums import SubmissionStatus
from backend.repository.task_repository import _get_task
from backend.repository.file_repository import get_file_by_id
from backend.repository.submission_repository import get_next_attempt_number, mark_previous_submissions_not_latest, get_student_submissions as _get_student_submissions, get_submission
from backend.repository.rubric_repository import get_accepted_rubric
from backend.schemas.submission import SubmissionDetailResponse
from backend.services.file_service import save_upload
from fastapi import HTTPException, status
from backend.models.enums import UserRole
from backend.models.users import User




async def create_submission_with_file(
    task_id: int,
    student_id: int,
    submission_text: str | None,
    team_id: int | None,
    file: UploadFile | None,
    db: AsyncSession,
) -> Submission:
    submission = Submission(
        task_id=task_id,
        student_id=student_id,
        submission_text=submission_text,
        
        team_id=team_id,
        status="submitted",
    )
    db.add(submission)
    await db.flush()  # Generates submission.id

    # 2. If a file was uploaded, process and attach it atomically
    if file and file.filename:
        file_record = await save_upload(
            file=file,
            owner_id=student_id,
            purpose="submission",
            task_id=task_id,
            submission_id=submission.id,  # Direct foreign key linkage
            db=db,
        )

    await db.commit()
    await db.refresh(submission)
    return submission


async def create_submission(
    task_id: int,
    student_id: int,
    db: AsyncSession,
    submission_text: str = "",
    file_id: int | None = None,
    team_id: int | None = None,
) -> Submission:
    """
    A submission must contain either text or an uploaded file.
    Each new submission becomes the latest attempt, while the
    previous latest submission is marked as no longer latest.
    Raises:
        HTTPException 404: Task or file not found.
        HTTPException 400: Submission has no content.
    """

    await _get_task(task_id, db)

    if not submission_text.strip() and file_id is None:
        raise HTTPException(
            status_code=400,
            detail="Submission must include text or an uploaded file.",
        )

    file_record = None

    if file_id is not None:
        file_record = await get_file_by_id(file_id, db)

        if file_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"File {file_id} not found.",
            )

        if file_record.owner_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to submit this file.",
            )

        if file_record.task_id not in (None, task_id):
            raise HTTPException(
                status_code=400,
                detail="File does not belong to this task.",
            )

    attempt_number = await get_next_attempt_number(
        task_id=task_id,
        student_id=student_id,
        db=db,
    )

    await mark_previous_submissions_not_latest(
        task_id=task_id,
        student_id=student_id,
        db=db,
    )

    rubric = await get_accepted_rubric(task_id, db)

    submission = Submission(
        task_id=task_id,
        student_id=student_id,
        team_id=team_id,
        rubric_id=rubric.id if rubric else None,
        attempt_number=attempt_number,
        is_latest=True,
        status=SubmissionStatus.pending,
        feedback=None,
    )

    db.add(submission)
    await db.flush()

    if file_record is not None:
        file_record.submission_id = submission.id

    await db.commit()
    await db.refresh(submission)

    return submission


async def get_student_submissions(
    task_id: int,
    student_id: int,
    db: AsyncSession,
) -> list[Submission]:
    """
    Return all submissions made by a student for a task,
    ordered from earliest attempt to latest.
    """

    await _get_task(task_id, db)

    return await _get_student_submissions(
        task_id=task_id,
        student_id=student_id,
        db=db,
    )
async def get_submission_details(
    submission_id: int,
    current_user: User,
    db: AsyncSession,
) -> SubmissionDetailResponse:
    """Retrieve details for a single submission, checking permissions."""
    submission = await get_submission(submission_id, db)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found.",
        )

    # Permission check: Students can only view their own submissions
    is_student = current_user.role == UserRole.student or current_user.role == "student"
    if is_student and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own submission details.",
        )

    return SubmissionDetailResponse.model_validate(submission)