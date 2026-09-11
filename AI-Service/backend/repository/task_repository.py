from __future__ import annotations
from fastapi import HTTPException
from backend.models.tasks import Task
from backend.services.exceptions import TaskNotFound

from sqlalchemy import select , or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import datetime as dt

async def _get_task(task_id: int, db: AsyncSession) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id).options(
            selectinload(Task.lab_details),
            selectinload(Task.assignment_details),
            selectinload(Task.project_details),
        )
    )

    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    return task




async def list_tasks(
    db: AsyncSession,
    cohort_year: int | None = None,
    major: str | None = None,
    task_type: str | None = None,
    filter_due_tasks: bool = False,
) -> list[Task]:

    query = select(Task).options(
        selectinload(Task.lab_details),
        selectinload(Task.assignment_details),
        selectinload(Task.project_details),
    )

    if cohort_year is not None:
        query = query.where(Task.target_cohort_year == cohort_year)

    if major is not None:
        query = query.where(
            or_(
                Task.target_major == major,
                Task.target_major.is_(None),
            )
        )

    if task_type is not None:
        query = query.where(Task.type == task_type)

    if filter_due_tasks:
        now_utc = dt.datetime.now(dt.timezone.utc)
        query = query.where(Task.due_date >= now_utc)

    query = query.order_by(Task.due_date.asc())

    result = await db.execute(query)

    return list(result.scalars().all())