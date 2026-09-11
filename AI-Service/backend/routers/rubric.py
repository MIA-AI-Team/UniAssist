"""
Rubric endpoints:
    POST   /tasks/{task_id}/rubrics/suggest
    POST   /tasks/{task_id}/rubrics/refine
    PATCH  /tasks/{task_id}/rubrics/status
    GET    /tasks/{task_id}/rubrics
"""

from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import require_professor, require_staff
from backend.database import get_db
from backend.models.users import User   
from backend.services.rubric_service import (
    list_rubrics,
    refine_rubric,
    set_rubric_status,
    suggest_rubric,
    create_manual_rubric,
)
from backend.schemas.rubric import RubricUploadResponse, CreateRubricRequest, RefineRequest, StatusRequest


router = APIRouter(
    prefix="/tasks/{task_id}/rubrics",
    tags=["Rubrics"],
)




@router.post("/suggest", status_code=201)
async def suggest(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Staff triggers AI to suggest a rubric."""

    rubric = await suggest_rubric(
        task_id,
        db,
    )

    return RubricUploadResponse(
        rubric_id=rubric.id,
        version=rubric.version,
        status=rubric.status,
    )

@router.post("/refine", status_code=201)
async def refine(
    task_id: int,
    body: RefineRequest,
    rubric_id: Optional[int] = None,
    version: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Staff provides feedback and AI creates a refined rubric version."""

    rubric = await refine_rubric(
        task_id,
        rubric_id,
        version,
        body.staff_feedback,
        db,
    )

    return RubricUploadResponse(
        rubric_id=rubric.id,
        version=rubric.version,
        status=rubric.status,
    )

@router.post("/create", status_code=201)
async def create(
    task_id: int,
    body: CreateRubricRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Staff manually creates a rubric (no AI involved)."""

    rubric = await create_manual_rubric(
        task_id,
        body.criteria,
        db,
    )

    return {
        "rubric_id": rubric.id,
        "version": rubric.version,
        "status": rubric.status,
        "criteria": [
            {
                "name": criterion.name,
                "description": criterion.description,
                "max_points": criterion.max_points,
                "sort_order": criterion.sort_order,
            }
            for criterion in sorted(rubric.criteria, key=lambda c: c.sort_order)
        ],
    }

@router.patch("/status")
async def update_status(
    body: StatusRequest,
    task_id:int,
    rubric_id: Optional[int] = None,
    version: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    """Professor accepts or rejects a rubric."""

    rubric = await set_rubric_status(
        task_id,
        version,
        rubric_id,
        body.status,
        current_user.id,
        db,
    )

    return RubricUploadResponse(
        rubric_id=rubric.id,
        version=rubric.version,
        status=rubric.status,
    )


@router.get("")
async def list_all_rubrics(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """List all rubric versions for a task."""

    rubrics = await list_rubrics(
        task_id,
        db,
    )

    return [
        {
            "id": rubric.id,
            "version": rubric.version,
            "source": rubric.source,
            "status": rubric.status,
            "reviewed_at": rubric.reviewed_at,
            "criteria": [
                {
                    "name": criterion.name,
                    "description": criterion.description,
                    "max_points": criterion.max_points,
                    "sort_order": criterion.sort_order,
                }
                for criterion in sorted(
                    rubric.criteria,
                    key=lambda criterion: criterion.sort_order,
                )
            ],
        }
        for rubric in rubrics
    ]
