from __future__ import annotations
from backend.models.enums import RubricStatus
from backend.models.rubric import Rubric, RubricCriteria
from backend.services.exceptions import NoAcceptedRubric


from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException





async def _get_rubric_with_criteria(db: AsyncSession,rubric_id: int=None, task_id:int=None, version:int=None  ) -> Rubric:
    """Helper to fetch a rubric with its criteria eagerly loaded."""
    if rubric_id is not None:
        result = await db.execute(
            select(Rubric)
            .where(Rubric.id == rubric_id)
            .options(selectinload(Rubric.criteria))
        )
        rubric = result.scalar_one_or_none()
        if rubric is None:
            raise HTTPException(status_code=404, detail=f"Rubric {rubric_id} not found.")
        if task_id is not None and rubric.task_id != task_id:
            raise HTTPException(status_code=422, detail="Rubric does not belong to this task.")
        return rubric
    elif task_id is not None and version ==0:
        result = await db.execute(
            select(Rubric)
            .where(Rubric.task_id == task_id)
            .options(selectinload(Rubric.criteria))
            .order_by(Rubric.version.desc())
            .limit(1)
        )
        rubric = result.scalar_one_or_none()
        if rubric is None:
            raise HTTPException(status_code=404, detail=f"No rubrics found for task {task_id}.")
        return rubric
    elif task_id is not None and version is not None:
        result = await db.execute(
            select(Rubric)
            .where(Rubric.task_id == task_id, Rubric.version == version)
            .options(selectinload(Rubric.criteria))
        )
        rubric = result.scalar_one_or_none()
        if rubric is None:
            raise HTTPException(status_code=404, detail=f"Rubric for task {task_id} with version {version} not found.")
        return rubric
    else:
        raise HTTPException(status_code=400, detail="Either rubric_id or both task_id and version must be provided.")





async def get_accepted_rubric(
    task_id: int,
    db: AsyncSession,
) -> Rubric:
    result = await db.execute(
        select(Rubric)
        .where(
            Rubric.task_id == task_id,
            Rubric.status == RubricStatus.accepted,
        )
        .options(selectinload(Rubric.criteria))
        .order_by(Rubric.version.desc())
        .limit(1)
    )

    rubric = result.scalar_one_or_none()

    if rubric is None:
        raise NoAcceptedRubric(
            f"Task {task_id} has no accepted rubric."
        )

    return rubric


async def get_next_rubric_version(
    task_id: int,
    db: AsyncSession,
) -> int:
    result = await db.execute(
        select(func.max(Rubric.version))
        .where(Rubric.task_id == task_id)
    )

    latest_version = result.scalar() or 0

    return latest_version + 1


async def  create_rubric(
    task_id: int,
    criteria: list,
    source,
    status,
    db: AsyncSession,
) -> Rubric:
    from backend.models.tasks import Task
    await db.execute(select(Task.id).where(Task.id == task_id).with_for_update())
    version = await get_next_rubric_version(task_id, db)

    rubric = Rubric(
        task_id=task_id,
        version=version,
        source=source,
        status=status,
    )

    db.add(rubric)
    await db.flush()

    for index, criterion in enumerate(criteria, start=1):
        db.add(
            RubricCriteria(
                rubric_id=rubric.id,
                name=criterion.name,
                description=criterion.description or "",
                max_points=criterion.max_points,
                sort_order=(
                    criterion.sort_order
                    if criterion.sort_order is not None
                    else index
                ),
            )
        )

    await db.commit()

    result = await _get_rubric_with_criteria(rubric_id=rubric.id, db=db)

    if result is None:
        raise RuntimeError(
            f"Failed to reload rubric {rubric.id}."
        )

    return result


async def replace_accepted_rubrics(
    task_id: int,
    except_rubric_id: int,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Rubric).where(
            Rubric.task_id == task_id,
            Rubric.status == RubricStatus.accepted,
            Rubric.id != except_rubric_id,
        )
    )

    for rubric in result.scalars().all():
        rubric.status = RubricStatus.replaced
async def get_rubrics_for_task(
     task_id: int, 
     db: AsyncSession,
 ) -> list[Rubric]:
     
     result = await db.execute( 
         select(Rubric) .where(
             Rubric.task_id == task_id
             ) .options(selectinload(Rubric.criteria)) 
             .order_by(Rubric.version.desc()) ) 
     return list(result.scalars().all())
