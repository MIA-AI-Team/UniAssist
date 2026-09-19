"""
Task endpoints:
    POST   /tasks              — staff creates a task
    GET    /tasks              — list tasks (filtered for students)
    GET    /tasks/{id}         — get single task
    DELETE /tasks/{id}         — professor deletes a task
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, require_staff, require_professor
from backend.database import get_db
from backend.models.enums import UserRole
from backend.models import Task, User
from backend.schemas.task import (
    CreateTaskRequest,
    TaskCreatedResponse,
    TaskDetailResponse,
    TaskListItemResponse,
)
from backend.repository import list_tasks
from backend.services.task_service import create_task, get_task
from backend.services.access import check_task_access, eligibility
from backend.services.submission_service import summary
from backend.models.submissions import Submission
from backend.models.users import Student
from backend.models.enums import SubmissionStatus
from backend.schemas.submission import SubmissionQueueItem
from backend.repository.rubric_repository import get_accepted_rubric
from backend.services.exceptions import NoAcceptedRubric

router = APIRouter(prefix="/tasks", tags=["Tasks"])





@router.post("/", status_code=201, response_model=TaskCreatedResponse)
async def create(
    body: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Professor or TA creates a new task."""
    return await create_task(body.model_dump(), current_user.id, db)


@router.get("/", response_model=list[TaskListItemResponse])
async def list_all(
    cohort_year: Optional[int] = None,
    major: Optional[str] = None,
    task_type: Optional[str] = None,
    filter_due_tasks: bool = Query(
        False, description="Filter for tasks whose due date has not passed"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List tasks. Students automatically filter by their cohort + major and if the task is not due.
    Staff can see all tasks or filter manually.
    """
    is_student = current_user.role == UserRole.student or current_user.role == "student"

    if is_student and getattr(current_user, "student", None):
        cohort_year = current_user.student.cohort_year
        major = current_user.student.major

    tasks = await list_tasks(
        db,
        cohort_year=cohort_year,
        major=major,
        task_type=task_type,
        filter_due_tasks=filter_due_tasks,
    )
    ids = [t.id for t in tasks]
    latest = {}
    counts = {}
    if is_student:
        rows = await db.scalars(select(Submission).where(Submission.task_id.in_(ids),
            Submission.student_id == current_user.id, Submission.is_latest.is_(True)))
        latest = {s.task_id: summary(s, student=True) for s in rows}
    else:
        rows = await db.execute(select(Submission.task_id, Submission.status, func.count()).where(
            Submission.task_id.in_(ids), Submission.is_latest.is_(True)).group_by(Submission.task_id, Submission.status))
        for task_id, status, count in rows:
            counts.setdefault(task_id, {})[status.value] = count
    return [TaskListItemResponse.model_validate(t).model_copy(update={
        "latest_submission": latest.get(t.id), "review_counts": None if is_student else counts.get(t.id, {})}) for t in tasks]


@router.get("/{task_id}/submissions", response_model=list[SubmissionQueueItem])
async def task_submissions(task_id: int, latest_only: bool = True, status: Optional[SubmissionStatus] = None,
                           db: AsyncSession = Depends(get_db), current_user: User = Depends(require_staff)):
    await get_task(task_id, db)
    query = select(Submission, User.name, Student.student_number).join(User, User.id == Submission.student_id).join(
        Student, Student.user_id == Submission.student_id).where(Submission.task_id == task_id)
    if latest_only:
        query = query.where(Submission.is_latest.is_(True))
    if status:
        query = query.where(Submission.status == status)
    rows = await db.execute(query.order_by(Submission.submitted_at.desc()))
    return [SubmissionQueueItem(**summary(s).model_dump(), student_id=s.student_id,
        student_name=name, student_number=number) for s, name, number in rows]


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_one(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single task with its type-specific details."""
    task = await get_task(task_id, db)
    check_task_access(task, current_user)
    accepted_rubric = None
    try:
        rubric = await get_accepted_rubric(task_id, db)
        accepted_rubric = {
            "id": rubric.id, "version": rubric.version,
            "total": sum(c.max_points for c in rubric.criteria),
            "criteria": [{"name": c.name, "description": c.description,
                          "max_points": c.max_points, "sort_order": c.sort_order}
                         for c in sorted(rubric.criteria, key=lambda c: c.sort_order)],
        }
    except NoAcceptedRubric:
        pass
    data = {key: getattr(task, key) for key in ("id", "type", "title", "description", "due_date",
        "target_cohort_year", "target_major", "reference_file_id", "created_by", "created_at",
        "lab_details", "assignment_details", "project_details")}
    return TaskDetailResponse(**data, accepted_rubric=accepted_rubric,
                              submission_eligibility=await eligibility(task, current_user, db))


@router.delete("/{task_id}", status_code=204)
async def delete(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    """
    Professor deletes a task.
    Cascades to all related rows: rubrics, submissions, files, chat sessions.
    TAs cannot delete tasks.
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task: Task | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    # Database cascades preserve referential ordering, including historical attempts.
    await db.execute(sql_delete(Task).where(Task.id == task_id))
    await db.commit()
