from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.dependencies import require_student,require_roles
from backend.database import get_db
from backend.models.users import User
from backend.schemas.repository import (RepositoryProposal,RepositoryAction,RepositoryInfo,RepositoryList,
    RepositoryReceipt,CommitList,SnapshotRequest,SnapshotInfo,RepositoryEventList)
from backend.services import repository_service as service

router=APIRouter(tags=["Public GitHub evidence"])
academic=require_roles(["student","teaching_assistant","professor"])


@router.post("/teams/{team_id}/repositories",response_model=RepositoryInfo,status_code=201)
async def propose(team_id:int,body:RepositoryProposal,user:User=Depends(require_student),db:AsyncSession=Depends(get_db)):
    return await service.propose(team_id,body,user,db)


@router.get("/teams/{team_id}/repositories",response_model=RepositoryList)
async def listing(team_id:int,before:int|None=Query(None,gt=0),limit:int=Query(20,ge=1,le=50),
                  user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.listing(team_id,user,db,before,limit)


@router.get("/repositories/{repository_id}",response_model=RepositoryInfo)
async def detail(repository_id:int,user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.detail(repository_id,user,db)


@router.post("/repositories/{repository_id}/actions",response_model=RepositoryReceipt)
async def actions(repository_id:int,body:RepositoryAction,user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.actions(repository_id,body,user,db)


@router.get("/repositories/{repository_id}/commits",response_model=CommitList)
async def commits(repository_id:int,before:int|None=Query(None,gt=0),limit:int=Query(20,ge=1,le=50),
                  user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.commits(repository_id,user,db,before,limit)


@router.get("/repositories/{repository_id}/history",response_model=RepositoryEventList)
async def history(repository_id:int,before:int|None=Query(None,gt=0),limit:int=Query(20,ge=1,le=50),
                  user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.history(repository_id,user,db,before,limit)


@router.post("/repositories/{repository_id}/snapshots",response_model=SnapshotInfo,status_code=201)
async def snapshot(repository_id:int,body:SnapshotRequest,user:User=Depends(require_student),db:AsyncSession=Depends(get_db)):
    return await service.capture(repository_id,body,user,db)


@router.get("/repository-snapshots/{snapshot_id}",response_model=SnapshotInfo)
async def snapshot_detail(snapshot_id:int,user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    return await service.snapshot_access(snapshot_id,user,db)


@router.get("/repository-snapshots/{snapshot_id}/download")
async def download(snapshot_id:int,user:User=Depends(academic),db:AsyncSession=Depends(get_db)):
    snapshot=await service.snapshot_access(snapshot_id,user,db)
    await db.refresh(snapshot,attribute_names=["archive"])
    return Response(snapshot.archive,media_type="application/zip",headers={"Cache-Control":"private, no-store",
        "X-Content-Type-Options":"nosniff","Content-Disposition":f'attachment; filename="repository-{snapshot.id}-{snapshot.commit_sha}.zip"'})
