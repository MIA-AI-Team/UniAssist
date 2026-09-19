"""Deterministic provider/concurrency boundaries against real PostgreSQL, no live GitHub."""
import asyncio
import datetime as dt
import uuid
import httpx
import pytest
from sqlalchemy import select,func
from test_ai_transactions import app,engine
from backend.database import AsyncSessionLocal
from backend.models.repository import Repository,RepositorySnapshot,Commit
from backend.services import github_client as github
from backend.services.access import fail


@pytest.mark.asyncio
async def test_repository_replacement_sync_failure_and_frozen_offline_evidence(monkeypatch):
    monkeypatch.setenv("GITHUB_FIXTURE_MODE","true")
    tag=uuid.uuid4().hex[:12]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as c:
        users={}
        for role in ("professor","student"):
            body=dict(name=role,email=f"{role}-{tag}@example.com",password="Verify-password-123",role=role,
                staff_role=role,department="CS",student_number=tag,cohort_year=2027,major="CS")
            assert (await c.post("/auth/register",json=body)).status_code==201
            login=(await c.post("/auth/login",json={"email":body["email"],"password":body["password"]})).json()
            users[role]={"Authorization":"Bearer "+login["access_token"]}
        staff,student=users["professor"],users["student"]
        async def post(path,headers,body,status=200):
            result=await c.post(path,headers=headers,json=body)
            assert result.status_code==status,result.text
            return result.json()
        task=(await post("/tasks/",staff,{"type":"project","require_team":True,"title":"Repository transaction",
            "description":"Explain your code","due_date":(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1)).isoformat(),"target_cohort_year":2027},201))["id"]
        rubric=await post(f"/tasks/{task}/rubrics/create",staff,{"criteria":[{"name":"Clarity","max_points":20}]},201)
        assert (await c.patch(f"/tasks/{task}/rubrics/status?rubric_id={rubric['rubric_id']}",headers=staff,json={"status":"accepted"})).status_code==200
        team=(await post(f"/tasks/{task}/teams",student,{"request_id":str(uuid.uuid4()),"name":"Evidence team"},201))["id"]
        await post(f"/teams/{team}/actions",student,{"request_id":str(uuid.uuid4()),"expected_version":1,"action":"request_approval"})
        await post(f"/teams/{team}/actions",staff,{"request_id":str(uuid.uuid4()),"expected_version":2,"action":"approve"})
        repos=[]
        for name in ("demo","replacement"):
            repos.append((await post(f"/teams/{team}/repositories",student,{"request_id":str(uuid.uuid4()),"repo_url":"uniassist-fixtures/"+name},201))["id"])
        async def approve(rid):
            return await post(f"/repositories/{rid}/actions",staff,{"request_id":str(uuid.uuid4()),"expected_version":1,"action":"approve"})
        await asyncio.gather(*(approve(rid) for rid in repos))
        rows=(await c.get(f"/teams/{team}/repositories",headers=student)).json()["items"]
        assert sum(r["status"]=="approved" for r in rows)==1
        assert sum(r["status"]=="superseded" for r in rows)==1
        active=next(r for r in rows if r["status"]=="approved")
        rid=active["id"]
        body={"request_id":str(uuid.uuid4()),"expected_version":active["version"],"action":"sync"}
        original=github.recent
        async def unavailable(*args):fail("github_rate_limit","Fixture rate limit",429)
        monkeypatch.setattr(github,"recent",unavailable)
        failure=await c.post(f"/repositories/{rid}/actions",headers=student,json=body)
        assert failure.status_code==429
        state=(await c.get(f"/repositories/{rid}",headers=student)).json()
        assert state["last_synced_at"] is None and state["sync_error"]=="github_rate_limit" and state["version"]==active["version"]
        monkeypatch.setattr(github,"recent",original)
        receipts=await asyncio.gather(*(post(f"/repositories/{rid}/actions",student,body) for _ in range(2)))
        assert receipts[0]==receipts[1]
        async with AsyncSessionLocal() as db:
            assert await db.scalar(select(func.count()).select_from(Commit).where(Commit.repository_id==rid))==1
        capture_body={"request_id":str(uuid.uuid4()),"commit_sha":"a"*40}
        saved=await asyncio.gather(*(post(f"/repositories/{rid}/snapshots",student,capture_body,201) for _ in range(2)))
        assert saved[0]["id"]==saved[1]["id"]
        sid=(await post("/submissions/",student,{"task_id":task,"repository_snapshot_id":saved[0]["id"],"submission_text":"My explanation"},201))["submission_id"]
        before=(await c.get(f"/repository-snapshots/{saved[0]['id']}/download",headers=student)).content
        replacement_name="replacement" if active["full_name"].endswith("/demo") else "demo"
        replacement=await post(f"/teams/{team}/repositories",student,{"request_id":str(uuid.uuid4()),"repo_url":"uniassist-fixtures/"+replacement_name},201)
        await approve(replacement["id"])
        assert (await c.get(f"/repositories/{rid}",headers=student)).json()["status"]=="superseded"
        async def no_network(*args,**kwargs):raise AssertionError("Saved evaluation must never fetch GitHub")
        monkeypatch.setattr(github,"metadata",no_network)
        monkeypatch.setattr(github,"archive",no_network)
        assert (await c.post(f"/submissions/{sid}/grade",headers=staff)).status_code==200
        assert (await c.get(f"/repository-snapshots/{saved[0]['id']}/download",headers=student)).content==before
        # Mutation receipts never duplicate archives and replacing a link never deletes old history.
        async with AsyncSessionLocal() as db:
            assert await db.scalar(select(func.count()).select_from(RepositorySnapshot).where(RepositorySnapshot.repository_id==rid))==1
            assert await db.scalar(select(func.count()).select_from(Repository).where(Repository.team_id==team))==3
    await engine.dispose()
