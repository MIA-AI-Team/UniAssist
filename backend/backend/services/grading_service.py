"""
Handles submission grading lifecycle:
    - grade_submission()    — call AI, persist grade + code reviews
    - confirm_final_grade() — professor confirms/overrides, sets staff_confirmed
"""

from __future__ import annotations

import datetime as dt
from zipfile import BadZipFile
from pypdf.errors import PdfReadError
from fastapi.concurrency import run_in_threadpool

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.access import lock_attempts, fail
from backend.repository.embedding_repository import get_reference_text

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
from backend.services.teaching_service import latest_guidance



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
    await lock_attempts(db, submission.task_id, submission.student_id, wait=False)
    await db.refresh(submission, attribute_names=["status", "is_latest"])
    if not submission.is_latest or submission.status != SubmissionStatus.pending:
        fail("attempt_not_pending", "Only the latest pending attempt can be evaluated.")
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

    reference_text = await get_reference_text(submission.task_id, db) or task.description

    submission_file = next(
        (
            file
            for file in submission.files
            if file.purpose == "submission"
        ),
        None,
    )

    submission_text, code_files = submission.submission_text, {}
    repository_warnings=[]
    if submission.repository_snapshot_id:
        from backend.models.repository import RepositorySnapshot
        from backend.services.github_client import inspect_archive
        import hashlib
        snapshot=await db.get(RepositorySnapshot,submission.repository_snapshot_id)
        await db.refresh(snapshot,attribute_names=["archive"])
        if hashlib.sha256(snapshot.archive).hexdigest()!=snapshot.provenance["archive_sha256"]:
            fail("repository_integrity","Stored repository evidence failed its integrity check.",409)
        _,repo_text,code_files=await run_in_threadpool(inspect_archive,snapshot.archive)
        submission_text="\n\n".join(p for p in (submission_text,repo_text) if p)
        repository_warnings.append("Repository commit: "+snapshot.commit_sha)
        if snapshot.provenance["omitted_files"]:
            repository_warnings.append("Some binary, unsupported or oversized repository files were excluded from AI input; see the snapshot manifest.")
        if snapshot.provenance["is_fixture"]:
            repository_warnings.append("DEMO: deterministic GitHub fixture, not real repository evidence.")
    try:
        if submission_file:
            file_text, code_files = await run_in_threadpool(extract_submission_content, submission_file.storage_path)
            submission_text = "\n\n".join(part for part in (submission.submission_text, file_text) if part)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except (ValueError, PdfReadError, BadZipFile) as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    submission_text, code_files, warnings = prepare_submission_for_grading(
        submission_text=submission_text,
        code_files=code_files,
    )
    warnings=repository_warnings+list(warnings)

    if not submission_text and not code_files:
        raise HTTPException(
            status_code=400,
            detail="Submission has no readable content to grade.",
        )

    guidance = await latest_guidance(submission.task_id, db)
    request = GradeSubmissionRequest(
        task_title=task.title,
        task_type=task.type.value,
        reference_text=reference_text,
        rubric_criteria=rubric_criteria,
        submission_text=submission_text,
        code_files=code_files,
        grading_key=guidance.content if guidance else None,
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
    submission.grading_guidance_id = guidance.id if guidance else None
    await db.refresh(submission, attribute_names=["is_latest", "status"])
    if not submission.is_latest or submission.status != SubmissionStatus.pending:
        fail("attempt_changed", "Attempt changed while evaluation was running.")
    submission.total_possible_grade = sum(c.max_points for c in rubric.criteria)
    submission.criterion_evaluations = [c.model_dump(mode="json") for c in result.criterion_evaluations]
    submission.ai_warnings = list(warnings) + list(result.warnings)
    submission.is_mock = ai.engine.mock_mode
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
    await lock_attempts(db, submission.task_id, submission.student_id, wait=False)
    await db.refresh(submission, attribute_names=["status", "is_latest"])
    if not submission.is_latest:
        fail("attempt_not_latest", "Only the latest attempt can be confirmed.")
    if submission.status != SubmissionStatus.ai_graded:
        raise HTTPException(
            status_code=422,
            detail=(
                "Submission must be AI graded before a professor "
                "can confirm the final grade."
            ),
        )

    import math
    if not math.isfinite(final_grade) or not 0 <= final_grade <= sum(c.max_points for c in submission.rubric.criteria):
        raise HTTPException(
            status_code=400,
            detail="Final grade must be between zero and the associated rubric total.",
        )

    submission.final_grade = final_grade
    submission.confirmed_by = confirmed_by
    submission.confirmed_at = dt.datetime.now(dt.timezone.utc)
    submission.status = SubmissionStatus.staff_confirmed

    from backend.services.account_service import audit
    audit(db, confirmed_by, "grade.confirmed", "submission", submission.id)

    await db.commit()
    await db.refresh(submission)

    return submission
