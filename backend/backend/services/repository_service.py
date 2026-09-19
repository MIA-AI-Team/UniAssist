"""Staff-approved repository links; student-owned evidence and audited attribution."""
import asyncio
import datetime as dt
import hashlib
import json
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select,text,func
from backend.models.repository import Repository,Commit,RepositoryEvent,RepositorySnapshot
from backend.models.teams import TeamMember
from backend.schemas.repository import (RepositoryInfo,RepositoryList,RepositoryReceipt,CommitInfo,CommitList,
    SnapshotInfo,RepositoryEventInfo,RepositoryEventList)
from backend.services import github_client as github
from backend.services import team_service as teams
from backend.services.access import fail,eligibility


async def actor_lock(user,db):
    await db.execute(text("SELECT pg_advisory_xact_lock(:user,-777)"),{"user":user.id})


async def team_access(team_id,user,db,lock=False):
    team=await teams.load_team(team_id,db,lock=lock)
    await teams.project(team.task_id,user,db)
    member=await db.get(TeamMember,(team.id,user.id),populate_existing=True)
    if not teams.staff(user) and not (member and member.active):
        fail("not_found","Repository workspace not found.",404)
    return team


def ready(team):
    if team.status!="approved" or not team.approved_roster:
        fail("team_not_approved","Approve the complete team roster first.")


def usable(repo,team):
    ready(team)
    if repo.status!="approved" or repo.approved_team_version!=team.version:
        fail("repository_not_approved","This link needs approval for the current team roster.")


async def load(repo_id,user,db,lock=False):
    repo=await db.get(Repository,repo_id)
    if not repo:
        fail("not_found","Repository not found.",404)
    team=await team_access(repo.team_id,user,db,lock)
    if lock:
        await db.refresh(repo)
    return repo,team


def info(repo,team,user):
    reason=None
    if repo.status=="legacy": reason="repository_legacy"
    elif team.status!="approved": reason="team_not_approved"
    elif repo.status!="approved" or repo.approved_team_version!=team.version: reason="repository_not_approved"
    actions=[]
    if repo.status!="legacy" and team.status=="approved":
        if teams.staff(user) and repo.status in ("pending","rejected","approved"):
            if reason: actions=["approve","reject"]
        if reason is None:
            actions += ["sync"] + (["attribute"] if teams.staff(user) else ["snapshot"])
    return RepositoryInfo(id=repo.id,task_id=repo.task_id,team_id=repo.team_id,
        repo_url=repo.repo_url if repo.full_name else None,full_name=repo.full_name,status=repo.status,
        version=repo.version,approved_team_version=repo.approved_team_version,last_synced_at=repo.last_synced_at,
        sync_error=repo.sync_error,partial_history=repo.partial_history,is_fixture=repo.is_fixture,
        actions=actions,unavailable_reason=reason)


def digest(repo_id,body):
    return hashlib.sha256(json.dumps([repo_id,body.model_dump(mode="json")],sort_keys=True).encode()).hexdigest()


async def event(repo,body,user,db,action,details):
    from backend.services.account_service import audit
    audit(db,user.id,"repository."+action,"commit" if action=="attribute" else "repository",
          details["commit_id"] if action=="attribute" else repo.id, ["student_id"] if action=="attribute" else [])
    db.add(RepositoryEvent(repository_id=repo.id,actor_id=user.id,request_id=str(body.request_id),
        request_hash=digest(repo.id,body),action=action,version=repo.version,details=details))
    await db.commit()
    return RepositoryReceipt(repository_id=repo.id,version=repo.version)


async def propose(team_id,body,user,db):
    await actor_lock(user,db)
    team=await team_access(team_id,user,db,True)
    ready(team)
    full_name=github.canonical(body.repo_url)
    previous=await db.scalar(select(Repository).where(Repository.created_by==user.id,Repository.request_id==str(body.request_id)))
    if previous:
        if previous.team_id!=team.id or previous.full_name!=full_name:
            fail("request_conflict","Request ID already used.")
        return info(previous,team,user)
    if await db.scalar(select(RepositoryEvent.id).where(RepositoryEvent.actor_id==user.id,RepositoryEvent.request_id==str(body.request_id))):
        fail("request_conflict","Request ID already used.")
    if await db.scalar(select(Repository.id).where(Repository.team_id==team.id,Repository.full_name==full_name,
        Repository.status.in_(["pending","approved"]))):
        fail("repository_exists","This link is already pending or approved.")
    if await db.scalar(select(func.count()).select_from(Repository).where(Repository.team_id==team.id,Repository.status=="pending"))>=5:
        fail("repository_limit","Review existing proposals before adding more.",422)
    metadata=await github.metadata(full_name)
    repo=Repository(task_id=team.task_id,team_id=team.id,repo_url="https://github.com/"+full_name,full_name=full_name,
        github_id=metadata["id"],created_by=user.id,request_id=str(body.request_id),is_fixture=github.fixture_mode())
    db.add(repo)
    await db.flush()
    await event(repo,body,user,db,"propose",{"full_name":full_name,"team_version":team.version})
    return info(repo,team,user)


async def listing(team_id,user,db,before,limit):
    team=await team_access(team_id,user,db)
    q=select(Repository).where(Repository.team_id==team_id)
    if before: q=q.where(Repository.id<before)
    rows=list((await db.scalars(q.order_by(Repository.id.desc()).limit(limit+1))).all())
    return RepositoryList(items=[info(r,team,user) for r in rows[:limit]],next_cursor=rows[limit-1].id if len(rows)>limit else None)


async def detail(repo_id,user,db):
    repo,team=await load(repo_id,user,db)
    return info(repo,team,user)


async def actions(repo_id,body,user,db):
    await actor_lock(user,db)
    repo,team=await load(repo_id,user,db,True)
    old=await db.scalar(select(RepositoryEvent).where(RepositoryEvent.actor_id==user.id,RepositoryEvent.request_id==str(body.request_id)))
    if old:
        if old.request_hash!=digest(repo.id,body): fail("request_conflict","Request ID already used.")
        return RepositoryReceipt(repository_id=old.repository_id,version=old.version)
    if repo.version!=body.expected_version:
        fail("repository_changed","Repository changed. Refresh before continuing.")
    if body.action not in info(repo,team,user).actions:
        fail("permission_denied","This repository action is unavailable.",403)
    details={"team_version":team.version}
    if body.action=="approve":
        await github.metadata(repo.full_name,repo.github_id)
        previous=list((await db.scalars(select(Repository).where(Repository.team_id==team.id,Repository.status=="approved",Repository.id!=repo.id))).all())
        for row in previous:
            row.status="superseded"
            row.version+=1
        await db.flush() # release the partial unique index before approving replacement
        repo.status,repo.approved_team_version="approved",team.version
        details["supersedes"]=[row.id for row in previous]
    elif body.action=="reject":
        repo.status,repo.approved_team_version="rejected",None
    elif body.action=="sync":
        try:
            async with asyncio.timeout(55):
                await github.metadata(repo.full_name,repo.github_id)
                rows,partial=await github.recent(repo.full_name)
        except TimeoutError:
            repo.sync_error="github_unavailable"
            await db.commit()
            fail("github_unavailable","GitHub sync timed out.",503)
        except HTTPException as exc:
            repo.sync_error=(exc.headers or {}).get("X-Error-Code","github_unavailable")
            await db.commit()
            raise
        for row in rows:
            if not await db.scalar(select(Commit.id).where(Commit.repository_id==repo.id,Commit.commit_hash==row["commit_hash"])):
                db.add(Commit(repository_id=repo.id,**row))
        repo.partial_history,repo.last_synced_at,repo.sync_error=partial,teams.now(),None
        details.update(imported_shas=[r["commit_hash"] for r in rows],partial_history=partial)
    elif body.action=="attribute":
        commit=await db.get(Commit,body.commit_id)
        if not commit or commit.repository_id!=repo.id:
            fail("not_found","Commit not found.",404)
        if body.student_id is not None:
            member=await db.get(TeamMember,(team.id,body.student_id))
            if not member or not member.active or not member.accepted_at:
                fail("invalid_input","Choose a current consented team member.",422)
        details.update(commit_id=commit.id,previous_student_id=commit.student_id,student_id=body.student_id)
        commit.student_id,commit.attributed_by,commit.attributed_at=body.student_id,user.id,teams.now()
    repo.version+=1
    return await event(repo,body,user,db,body.action,details)


async def commits(repo_id,user,db,before,limit):
    await load(repo_id,user,db)
    q=select(Commit).where(Commit.repository_id==repo_id)
    if before:q=q.where(Commit.id<before)
    rows=list((await db.scalars(q.order_by(Commit.id.desc()).limit(limit+1))).all())
    items=[]
    for row in rows[:limit]:
        item=CommitInfo.model_validate(row)
        # Historical student_id alone was not a reviewed attribution.
        if item.attributed_at is None:item.student_id=None
        item.committed_at=item.committed_at.replace(tzinfo=dt.timezone.utc)
        items.append(item)
    return CommitList(items=items,next_cursor=rows[limit-1].id if len(rows)>limit else None)


async def history(repo_id,user,db,before,limit):
    await load(repo_id,user,db)
    q=select(RepositoryEvent).where(RepositoryEvent.repository_id==repo_id)
    if before:q=q.where(RepositoryEvent.id<before)
    rows=list((await db.scalars(q.order_by(RepositoryEvent.id.desc()).limit(limit+1))).all())
    return RepositoryEventList(items=[RepositoryEventInfo.model_validate(r) for r in rows[:limit]],
        next_cursor=rows[limit-1].id if len(rows)>limit else None)


async def capture(repo_id,body,user,db):
    await actor_lock(user,db)
    repo,team=await load(repo_id,user,db,True)
    previous=await db.scalar(select(RepositorySnapshot).where(RepositorySnapshot.owner_id==user.id,RepositorySnapshot.request_id==str(body.request_id)))
    if previous:
        if previous.repository_id!=repo_id or previous.commit_sha!=body.commit_sha:
            fail("request_conflict","Snapshot request ID already used.")
        return SnapshotInfo.model_validate(previous)
    usable(repo,team)
    task=await teams.project(team.task_id,user,db)
    access=await eligibility(task,user,db)
    if not access["allowed"]:fail(access["reason_code"],"Submission is not available.")
    try:
        async with asyncio.timeout(70):
            await github.metadata(repo.full_name,repo.github_id)
            data=await github.archive(repo.full_name,body.commit_sha)
            manifest,prose,code=await run_in_threadpool(github.inspect_archive,data)
    except TimeoutError:
        fail("github_unavailable","Snapshot capture timed out.",503)
    if not prose and not code:
        fail("repository_empty","No supported UTF-8 text or code files found.",422)
    access=await eligibility(task,user,db)
    if not access["allowed"]:fail(access["reason_code"],"Submission closed during capture.")
    attribution=list((await db.scalars(select(Commit).where(Commit.repository_id==repo.id,Commit.commit_hash==body.commit_sha))).all())
    snapshot=RepositorySnapshot(repository_id=repo.id,owner_id=user.id,request_id=str(body.request_id),commit_sha=body.commit_sha,
        archive=data,provenance={"task_id":repo.task_id,"team_id":team.id,"repository_id":repo.id,"repo_url":repo.repo_url,"github_id":repo.github_id,
        "commit_sha":body.commit_sha,"archive_sha256":hashlib.sha256(data).hexdigest(),"compressed_bytes":len(data),
        "captured_at":teams.now().isoformat(),"team_version":team.version,"repository_version":repo.version,
        "is_fixture":github.fixture_mode(),"files":manifest,"omitted_files":sum(not f["included"] for f in manifest),
        "attribution":[{"commit_sha":r.commit_hash,"student_id":r.student_id if r.attributed_at else None,
            "attributed_by":r.attributed_by,"attributed_at":r.attributed_at.isoformat() if r.attributed_at else None} for r in attribution]})
    db.add(snapshot)
    await db.commit()
    return SnapshotInfo.model_validate(snapshot)


async def snapshot_access(snapshot_id,user,db):
    snapshot=await db.get(RepositorySnapshot,snapshot_id)
    if not snapshot:fail("not_found","Snapshot not found.",404)
    repo=await db.get(Repository,snapshot.repository_id)
    await teams.project(repo.task_id,user,db)
    if not teams.staff(user) and snapshot.owner_id!=user.id:
        fail("submission_forbidden","This snapshot belongs to another student.",403)
    return snapshot


async def attach(snapshot_id,team,user,db):
    snapshot=await snapshot_access(snapshot_id,user,db)
    repo=await db.get(Repository,snapshot.repository_id)
    if not team or repo.team_id!=team.id:
        fail("team_forbidden","Snapshot belongs to another project team.",403)
    usable(repo,team)
    if snapshot.provenance["team_version"]!=team.version:
        fail("repository_changed","Capture a new snapshot for the approved roster.")
    return snapshot
