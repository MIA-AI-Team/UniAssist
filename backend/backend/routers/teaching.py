from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.dependencies import require_staff
from backend.database import get_db
from backend.models.users import User
from backend.schemas.teaching import (GuidanceCreate, GuidanceInfo, GuidanceList, TaskAnalytics,
    ReportCreate, TeachingReportInfo, TeachingReportList)
from backend.services import teaching_service as service

router = APIRouter(tags=["Staff teaching tools"])


@router.get("/tasks/{task_id}/grading-guidance", response_model=GuidanceList)
async def guidance(task_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                   user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.list_guidance(task_id, db, before, limit)


@router.get("/tasks/{task_id}/grading-guidance/{guidance_id}", response_model=GuidanceInfo)
async def guidance_version(task_id: int, guidance_id: int, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.guidance_detail(task_id, guidance_id, db)


@router.post("/tasks/{task_id}/grading-guidance", response_model=GuidanceInfo, status_code=201)
async def save_guidance(task_id: int, body: GuidanceCreate, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.create_guidance(task_id, body, user, db)


@router.get("/tasks/{task_id}/analytics", response_model=TaskAnalytics)
async def analytics(task_id: int, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    _, result, _ = await service.analytics_snapshot(task_id, db)
    return result


@router.get("/tasks/{task_id}/analytics/reports", response_model=TeachingReportList)
async def reports(task_id: int, before: int | None = Query(None, gt=0), limit: int = Query(10, ge=1, le=30),
                  user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.list_reports(task_id, db, before, limit)


@router.post("/tasks/{task_id}/analytics/reports", response_model=TeachingReportInfo, status_code=201)
async def generate(task_id: int, body: ReportCreate, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.generate_report(task_id, body, user, db)
