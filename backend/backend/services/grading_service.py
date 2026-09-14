"""
Handles submission grading lifecycle:
    - grade_submission()    — call AI, persist grade + code reviews
    - confirm_final_grade() — professor confirms/overrides, sets staff_confirmed
"""

from __future__ import annotations

import datetime as dt

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sympy import python

from ai_tutor import GradingResponseError
from ai_tutor.models import GradeSubmissionRequest, RubricCriteriaItem
from ai_tutor.parsers import  extract_submission_content, prepare_submission_for_grading

from backend.core.ai import ai
from backend.models.enums import ReviewType, Severity, SubmissionStatus
from backend.models.repository import CodeReview
from backend.models.submissions import Submission
from backend.repository.rubric_repository import get_accepted_rubric, _get_rubric_with_criteria
from backend.repository.submission_repository import get_submission
from backend.repository.task_repository import _get_task
from backend.services.task_context_service import get_task_context
from backend.services.ai_service import call_ai



async def grade_submission(
    submission_id: int,
    db: AsyncSession,
) -> Submission:
    """
    Grade a submission using its assigned rubric and submitted files.

    Raises:
        HTTPException 404 — submission, task, or rubric not found
        HTTPException 400 — submission has no readable content
        HTTPException 502 — AI grading failed
        HTTPException 503 — all LLM providers unavailable
    """

    submission = await get_submission(submission_id, db)
    task = await _get_task(submission.task_id, db)

    rubric = await _get_rubric_with_criteria(
        rubric_id=submission.rubric_id,
        db=db,
    )

    rubric_criteria = [
        RubricCriteriaItem(
            name=criterion.name,
            description=criterion.description or "",
            max_points=criterion.max_points,
            sort_order=criterion.sort_order,
        )
        for criterion in sorted(
            rubric.criteria,
            key=lambda criterion: criterion.sort_order,
        )
    ]

    context = await get_task_context(
        submission.task_id,
        db,
    )

    reference_text = context["reference_text"] or task.description

    submission_file = next(
        (
            file
            for file in submission.files
            if file.purpose == "submission"
        ),
        None,
    )

    if submission_file is None:
        raise HTTPException(
            status_code=400,
            detail="Submission has no files.",
        )

    try:
        submission_text, code_files = extract_submission_content(
            submission_file.storage_path
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    submission_text, code_files, warnings = prepare_submission_for_grading(
        submission_text=submission_text,
        code_files=code_files,
    )

    if not submission_text and not code_files:
        raise HTTPException(
            status_code=400,
            detail="Submission has no readable content to grade.",
        )

    request = GradeSubmissionRequest(
        task_title=task.title,
        task_type=task.type.value,
        reference_text=reference_text,
        rubric_criteria=rubric_criteria,
        submission_text=submission_text,
        code_files=code_files,
        request_metadata={
            "task_id": submission.task_id,
            "submission_id": submission_id,
            "rubric_id": rubric.id,
            "attempt_number": submission.attempt_number,
            "warnings": warnings,
        },
    )

    try:
        result = await call_ai(
            ai.grade_submission,
            request,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except GradingResponseError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    submission.ai_suggested_grade = result.ai_suggested_grade
    submission.feedback = result.summary_feedback
    submission.status = SubmissionStatus.ai_graded

    for finding in result.code_reviews:
        try:
            severity = Severity(finding.severity)
        except ValueError:
            severity = Severity.info

        db.add(
            CodeReview(
                submission_id=submission_id,
                commit_id=None,
                review_type=ReviewType.ai_code_review,
                severity=severity,
                finding=finding.finding,
                file_path=finding.file_path or "",
                line_number=finding.line_number,
            )
        )

    await db.commit()
    await db.refresh(submission)

    return submission

# ---------------------------------------------------------------------------
# Confirm final grade
# ---------------------------------------------------------------------------

async def confirm_final_grade(
    submission_id: int,
    final_grade: float,
    confirmed_by: int,
    db: AsyncSession,
) -> Submission:
    """
    Professor confirms or overrides the AI-suggested grade.

    Sets:
        final_grade
        confirmed_by
        confirmed_at
        status = staff_confirmed

    Raises:
        HTTPException 404 — submission not found
        HTTPException 422 — submission not yet AI graded
        HTTPException 400 — final grade out of range
    """

    submission = await get_submission(submission_id, db)

    if submission.status != SubmissionStatus.ai_graded:
        raise HTTPException(
            status_code=422,
            detail=(
                "Submission must be AI graded before a professor "
                "can confirm the final grade."
            ),
        )

    if final_grade < 0:
        raise HTTPException(
            status_code=400,
            detail="Final grade cannot be negative.",
        )

    submission.final_grade = final_grade
    submission.confirmed_by = confirmed_by
    submission.confirmed_at = dt.datetime.now(dt.timezone.utc)
    submission.status = SubmissionStatus.staff_confirmed

    await db.commit()
    await db.refresh(submission)

    return submission
