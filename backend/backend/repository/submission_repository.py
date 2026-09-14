from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.enums import RubricStatus
from backend.models.file import File
from backend.models.rubric import Rubric
from backend.models.submissions import Submission

async def get_student_submissions(
    task_id: int,
    student_id: int,
    db: AsyncSession,
) -> list[Submission]:
    result = await db.execute(
        select(Submission)
        .where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
        )
        .order_by(Submission.attempt_number.asc())
    )

    return list(result.scalars().all())


async def get_submission(
    submission_id: int,
    db: AsyncSession,
) -> Submission:
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.files))
    )

    submission = result.scalar_one_or_none()

    if submission is None:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} not found.",
        )

    return submission



async def get_next_attempt_number(
    task_id: int,
    student_id: int,
    db: AsyncSession,
) -> int:
    result = await db.execute(
        select(func.max(Submission.attempt_number)).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
        )
    )

    max_attempt = result.scalar_one_or_none()
    return (max_attempt or 0) + 1


async def mark_previous_submissions_not_latest(
    task_id: int,
    student_id: int,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Submission).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
            Submission.is_latest.is_(True),
        )
    )

    for submission in result.scalars().all():
        submission.is_latest = False

