"""
Handles rubric lifecycle:
    - suggest_rubric()      — call AI, persist RUBRICS + RUBRIC_CRITERIA
    - refine_rubric()       — call AI with staff feedback, persist as new version
    - set_rubric_status()   — professor accepts or rejects a rubric
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ai_tutor.models import (
    RubricCriteriaItem,
    RubricRefineRequest,
    RubricSuggestRequest,
)

from backend.core.ai import ai
from backend.models.enums import RubricSource, RubricStatus
from backend.models.rubric import Rubric
from backend.repository.embedding_repository import get_reference_text
from backend.repository.rubric_repository import (
    _get_rubric_with_criteria,
    create_rubric,
    replace_accepted_rubrics,
    get_rubrics_for_task,
)
from backend.repository.task_repository import _get_task
from backend.services.ai_service import call_ai
from sqlalchemy import select
from backend.models.tasks import Task


async def suggest_rubric(
    task_id: int,
    db: AsyncSession,
) -> Rubric:
    """
    Generate an AI-suggested rubric and save it
    as a new pending version.
    """

    task = await _get_task(task_id, db)

    reference_text = (
        await get_reference_text(task_id, db)
        or task.description
    )

    request = RubricSuggestRequest(
        task_title=task.title,
        task_type=task.type.value,
        task_description=task.description,
        reference_text=reference_text,
        request_metadata={
            "task_id": task_id,
        },
    )

    result = await call_ai(
        ai.suggest_rubric,
        request,
    )

    return await create_rubric(
        task_id=task_id,
        criteria=result.criteria,
        source=RubricSource.ai_suggested,
        status=RubricStatus.pending,
        db=db,
    )



async def create_manual_rubric(
    task_id: int,
    criteria: list,
    db: AsyncSession,
) -> Rubric:
    """
    Create a rubric directly from staff-provided criteria (no AI call).
    """

    await _get_task(task_id, db)  # 404s if task doesn't exist

    return await create_rubric(
        task_id=task_id,
        criteria=criteria,
        source=RubricSource.staff_created,
        status=RubricStatus.pending,
        db=db,
    )



async def refine_rubric(
    task_id: int,
    rubric_id: Optional[int] = None,
    version: Optional[int] = None,
    staff_feedback: str = "",
    db: AsyncSession = None,
) -> Rubric:
    """
    Refine an existing rubric using staff feedback
    and save the result as a new pending version.
    """

    task = await _get_task(task_id, db)

    rubric = await _get_rubric_with_criteria(
        rubric_id=rubric_id,
        task_id=task_id,
        version=version,
        db=db,
    )

    if rubric.task_id != task_id:
        raise HTTPException(
            status_code=400,
            detail="Rubric does not belong to this task.",
        )

    previous_criteria = [
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

    reference_text = (
        await get_reference_text(task_id, db)
        or task.description
    )

    request = RubricRefineRequest(
        task_title=task.title,
        task_type=task.type.value,
        task_description=task.description,
        reference_text=reference_text,
        previous_criteria=previous_criteria,
        staff_feedback=staff_feedback,
    )

    result = await call_ai(
        ai.refine_rubric,
        request,
    )

    return await create_rubric(
        task_id=task_id,
        criteria=result.criteria,
        source=RubricSource.ai_suggested,
        status=RubricStatus.pending,
        db=db,
    )


async def set_rubric_status(
    task_id: int,
    version: int,
    rubric_id: int,
    status: str,
    reviewed_by: int,
    db: AsyncSession,
) -> Rubric:
    """
    Accept or reject a rubric.
    """

    if status not in {
        "accepted",
        "rejected",
    }:
        raise HTTPException(
            status_code=422,
            detail="Status must be either 'accepted' or 'rejected'.",
        )
    await db.execute(select(Task.id).where(Task.id == task_id).with_for_update())
    rubric = await _get_rubric_with_criteria(
        db=db,
        rubric_id=rubric_id,
        task_id=task_id,
        version=version,
        
    )

    if status == "accepted":
        await replace_accepted_rubrics(
            task_id=rubric.task_id,
            except_rubric_id=rubric.id,
            db=db,
        )

    rubric.status = RubricStatus(status)
    rubric.reviewed_by = reviewed_by
    from backend.services.account_service import audit
    audit(db, reviewed_by, "rubric." + status, "rubric", rubric.id)
    rubric.reviewed_at = dt.datetime.now(
        dt.timezone.utc
    )

    await db.commit()

    result = await _get_rubric_with_criteria(
        rubric_id=rubric.id,
        db=db ,
    )

    return result
async def list_rubrics( 
    task_id: int, 
    db: AsyncSession,
) -> list[Rubric]: 
    """ 
    Return all rubric versions for a task. 
    """ 

    await _get_task(task_id, db) 
    return await get_rubrics_for_task( task_id, db, )
