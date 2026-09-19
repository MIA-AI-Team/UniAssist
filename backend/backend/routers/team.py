from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.dependencies import require_student, require_roles
from backend.database import get_db
from backend.models.users import User
from backend.schemas.team import (TeamCreate, TeamAction, InvitationReply, TeamInfo, TeamList,
    InvitationList, TeamMutationResult, TeamEventList)
from backend.services import team_service as service

router = APIRouter(tags=["Project teams"])
academic_user = require_roles(["student", "teaching_assistant", "professor"])


@router.post("/tasks/{task_id}/teams", response_model=TeamInfo, status_code=201)
async def create(task_id: int, body: TeamCreate, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.create(task_id, body, user, db)


@router.get("/tasks/{task_id}/teams", response_model=TeamList)
async def teams(task_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                status: str | None = Query(None, pattern="^(draft|awaiting_approval|approved|rejected|archived|legacy)$"),
                user: User = Depends(academic_user), db: AsyncSession = Depends(get_db)):
    return await service.list_teams(task_id, user, db, before, limit, status)


@router.get("/teams/{team_id}", response_model=TeamInfo)
async def detail(team_id: int, user: User = Depends(academic_user), db: AsyncSession = Depends(get_db)):
    return await service.detail(team_id, user, db)


@router.get("/teams/{team_id}/history", response_model=TeamEventList)
async def history(team_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                  user: User = Depends(academic_user), db: AsyncSession = Depends(get_db)):
    return await service.history(team_id, user, db, before, limit)


@router.post("/teams/{team_id}/actions", response_model=TeamMutationResult)
async def act(team_id: int, body: TeamAction, user: User = Depends(academic_user), db: AsyncSession = Depends(get_db)):
    return await service.act(team_id, body, user, db)


@router.get("/team-invitations", response_model=InvitationList)
async def invitations(before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                       user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.inbox(user, db, before, limit)


@router.post("/team-invitations/{invitation_id}/respond", response_model=TeamMutationResult)
async def respond(invitation_id: int, body: InvitationReply, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.respond(invitation_id, body, user, db)
