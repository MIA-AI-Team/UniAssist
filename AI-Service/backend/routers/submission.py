"""
    POST   /submissions                  — student submits work
    GET    /submissions/my/{task_id}     — student views their own submissions
    POST   /submissions/{id}/grade       — staff triggers AI grading
    PATCH  /submissions/{id}/confirm     — professor confirms final grade
    GET    /submissions/{id}             — get submission details
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_current_user,
    require_professor,
    require_staff,
    require_student,
)
from backend.database import get_db
from backend.models.users import User
from backend.schemas.submission import (
    ConfirmGradeRequest,
    CreateSubmissionForm,
    SubmissionConfirmedResponse,
    SubmissionCreatedResponse,
    SubmissionDetailResponse,
    SubmissionGradedResponse,
    SubmissionListItemResponse,
)
from backend.services.grading_service import (
    confirm_final_grade,
    grade_submission,
)
from backend.services.submission_service import (
    create_submission,
    get_student_submissions,
    get_submission_details,
)

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


@router.post("/", status_code=201, response_model=SubmissionCreatedResponse)
async def submit(
    body: CreateSubmissionForm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """Student submits work for a task."""
    submission = await create_submission(
        task_id=body.task_id,
        student_id=current_user.id,
        submission_text=body.submission_text,
        file_id=body.file_id,
        team_id=body.team_id,
        db=db,
    )

    return SubmissionCreatedResponse(
        submission_id=submission.id,
        task_id=submission.task_id,
        attempt_number=submission.attempt_number,
        status=submission.status,
        submitted_at=submission.submitted_at,
    )


@router.get("/my/{task_id}", response_model=list[SubmissionListItemResponse])
async def my_submissions(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """Student views all their submissions for a task."""
    return await get_student_submissions(
        task_id=task_id,
        student_id=current_user.id,
        db=db,
    )


@router.post("/{submission_id}/grade", response_model=SubmissionGradedResponse)
async def grade(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    """Staff triggers AI grading for a submission."""
    submission = await grade_submission(
        submission_id=submission_id,
        db=db,
    )

    return SubmissionGradedResponse(
        submission_id=submission.id,
        status=submission.status,
        ai_suggested_grade=submission.ai_suggested_grade,
        feedback=submission.feedback,
    )


@router.patch("/{submission_id}/confirm", response_model=SubmissionConfirmedResponse)
async def confirm(
    submission_id: int,
    body: ConfirmGradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    """Professor confirms or overrides the AI-suggested grade."""
    submission = await confirm_final_grade(
        submission_id=submission_id,
        final_grade=body.final_grade,
        confirmed_by=current_user.id,
        db=db,
    )

    return SubmissionConfirmedResponse(
        submission_id=submission.id,
        status=submission.status,
        final_grade=submission.final_grade,
        confirmed_by=submission.confirmed_by,
        confirmed_at=submission.confirmed_at,
    )


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
async def get_one(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get submission details including grade and code reviews."""
    return await get_submission_details(
        submission_id=submission_id,
        current_user=current_user,
        db=db,
    )