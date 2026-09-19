"""Shared academic rules for UI eligibility and mutations."""
import datetime as dt
from fastapi import HTTPException
from sqlalchemy import select, text
from backend.models.users import User
from backend.models.submissions import Submission
from backend.models.enums import UserRole, SubmissionStatus
from backend.repository.rubric_repository import get_accepted_rubric
from backend.services.exceptions import NoAcceptedRubric

def fail(code: str, message: str, status: int = 409):
    raise HTTPException(status_code=status, detail=message, headers={"X-Error-Code": code})

def check_task_access(task, user):
    if user.role == UserRole.student and (
        not user.student or task.target_cohort_year != user.student.cohort_year
        or (task.target_major and task.target_major != user.student.major)
    ):
        fail("task_forbidden", "This task is not assigned to your cohort and major.", 403)

async def lock_attempts(db, task_id: int, student_id: int, wait=True):
    # Covers the first attempt, for which there is no row to lock yet.
    if wait:
        await db.execute(text("SELECT pg_advisory_xact_lock(:task, :student)"), {"task": task_id, "student": student_id})
    else:
        acquired = await db.scalar(text("SELECT pg_try_advisory_xact_lock(:task, :student)"), {"task": task_id, "student": student_id})
        if not acquired:
            fail("review_in_progress", "Another submission or review is in progress. Refresh before retrying.")

async def eligibility(task, user, db):
    check_task_access(task, user)
    rubric = None
    try:
        rubric = await get_accepted_rubric(task.id, db)
    except NoAcceptedRubric:
        pass
    reason = None
    team_id = None
    if user.role != UserRole.student:
        reason = "student_only"
    elif await db.scalar(select(Submission.id).where(
        Submission.task_id == task.id, Submission.student_id == user.id,
        Submission.status == SubmissionStatus.staff_confirmed).limit(1)):
        reason = "grade_confirmed"
    elif dt.datetime.now(dt.timezone.utc) > task.due_date and not (
        task.assignment_details and task.assignment_details.allow_late
    ):
        reason = "deadline_passed"
    elif rubric is None:
        reason = "rubric_not_ready"
    if user.role == UserRole.student and task.project_details and task.project_details.require_team:
        from backend.services.team_service import submission_team
        team, team_reason = await submission_team(task, user, db)
        team_id = team.id if team else None
        reason = reason or team_reason
    return {"allowed": reason is None, "reason_code": reason,
            "rubric_ready": rubric is not None,
            "rubric_total": sum(c.max_points for c in rubric.criteria) if rubric else None, "team_id": team_id}

async def student_user(student_id, db):
    from sqlalchemy.orm import selectinload
    return await db.scalar(select(User).where(User.id == student_id).options(selectinload(User.student)))
