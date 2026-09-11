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
from sqlalchemy import select
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
        cohort_year = cohort_year or current_user.student.cohort_year
        major = major or current_user.student.major

    return await list_tasks(
        db,
        cohort_year=cohort_year,
        major=major,
        task_type=task_type,
        filter_due_tasks=filter_due_tasks,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_one(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single task with its type-specific details."""
    return await get_task(task_id, db)


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

    await db.delete(task)
    await db.commit()