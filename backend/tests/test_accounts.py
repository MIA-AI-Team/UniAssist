"""Phase 5 runs in its own fresh PostgreSQL database; never changes existing admins."""
import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
import asyncpg
import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from test_ai_transactions import app
from backend.database import get_db
from backend import bootstrap_admin
from backend.services import ai_service
from backend.services.exceptions import AIServiceError
from backend.models.operations import AIOperation, AuditEvent


@pytest.mark.asyncio
async def test_account_controls_privacy_audit_and_durable_metrics(monkeypatch):
    name = "verify_accounts_" + uuid.uuid4().hex[:12]
    connection = await asyncpg.connect("postgresql://verify:verify-local-only@localhost:15432/verify")
    await connection.execute(f'CREATE DATABASE "{name}"')
    await connection.close()
    url = f"postgresql+asyncpg://verify:verify-local-only@localhost:15432/{name}"
    root = Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root/"backend",
        env=dict(os.environ, DATABASE_URL=url, PYTHONPATH=str(root/"backend")), check=True, capture_output=True)
    engine = create_async_engine(url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async def isolated_db():
        async with sessions() as db:
            try:
                yield db
                await db.commit()
            except BaseException:
                await db.rollback()
                raise
    app.dependency_overrides[get_db] = isolated_db
    monkeypatch.setattr(bootstrap_admin, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(ai_service, "AsyncSessionLocal", sessions)
    password = "Verify-admin-password-123"
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            async def login(email):
                response = await client.post("/auth/login", json={"email":email,"password":password})
                assert response.status_code == 200, response.text
                return {"Authorization":"Bearer "+response.json()["access_token"]}
            async def update(uid, headers, **fields):
                current = await client.get(f"/admin/users/{uid}", headers=headers)
                return await client.patch(f"/admin/users/{uid}", headers=headers,
                    json={"expected_version":current.json()["profile_version"], **fields})
            blocked = await client.post("/auth/register", json={"name":"Public admin", "email":"blocked@example.com", "password":password,"role":"admin"})
            assert blocked.status_code == 422
            admin1 = await bootstrap_admin.bootstrap("Operator One", "operator1@example.com", password)
            a1 = await login("operator1@example.com")
            with pytest.raises(ValueError):
                await bootstrap_admin.bootstrap("Overwrite", "operator1@example.com", password)
            last = await update(admin1, a1, is_active=False)
            assert last.status_code == 409 and last.json()["code"] == "last_active_admin"
            admin2 = await bootstrap_admin.bootstrap("Operator Two", "operator2@example.com", password)
            a2 = await login("operator2@example.com")
            # Two concurrent self-suspensions can never remove both active admins.
            results = await asyncio.gather(update(admin1,a1,is_active=False), update(admin2,a2,is_active=False))
            assert sorted(r.status_code for r in results) == [200,409]
            active, inactive = (a1,admin2) if results[0].status_code==409 else (a2,admin1)
            assert (await update(inactive,active,is_active=True)).status_code == 200
            student = (await client.post("/auth/register", json=dict(name="Private Student",email="student@example.com",password=password,
                role="student",student_number="P5",cohort_year=2027,major="CS"))).json()["id"]
            staff = (await client.post("/auth/register", json=dict(name="Teaching Person",email="ta@example.com",password=password,
                role="teaching_assistant",staff_role="teaching_assistant",department="CS"))).json()["id"]
            s = await login("student@example.com")
            ta = await login("ta@example.com")
            for path in ("/admin/users", "/admin/audit", "/admin/ai-metrics"):
                assert (await client.get(path,headers=s)).status_code==403
                assert (await client.get(path,headers=ta)).status_code==403
            for path in ("/tasks/", "/submissions/1", "/files/1", "/files/1/download", "/chat-sessions/1", "/repository-snapshots/1"):
                assert (await client.get(path,headers=active)).status_code==403
            denied = await client.patch("/auth/me",headers=s,json={"expected_version":1,"name":"New Student","cohort_year":2030})
            assert denied.status_code==422
            good = await client.patch("/auth/me",headers=s,json={"expected_version":1,"name":"New Student","github_username":"student-demo"})
            assert good.status_code==200 and good.json()["github_username"]=="student-demo"
            stale = await client.patch("/auth/me",headers=s,json={"expected_version":1,"name":"Stale Name"})
            assert stale.status_code==409
            assert (await update(student,active,role="professor")).status_code==422
            assert (await update(student,active,email="ta@example.com")).status_code==409
            assert (await update(student,active,cohort_year=2028,major="Math",student_number="P5-corrected")).status_code==200
            assert (await update(staff,active,role="professor")).status_code==200
            # Existing JWT role claim cannot override current database authority.
            assert (await client.get("/auth/me",headers=ta)).json()["role"]=="professor"
            assert (await update(student,active,is_active=False)).status_code==200
            for path in ("/auth/me", "/tasks/", "/files/1/download"):
                response = await client.get(path,headers=s)
                assert response.status_code==401 and response.json()["code"]=="account_suspended"
            assert (await client.post("/auth/login",json={"email":"student@example.com","password":password})).status_code==401
            assert (await update(student,active,is_active=True)).status_code==200
            assert (await client.get("/auth/me",headers=s)).status_code==200
            results = await client.get("/admin/users?q=P5-corrected&limit=1",headers=active)
            assert results.json()["items"][0]["id"]==student
            logs = (await client.get("/admin/audit",headers=active)).json()
            assert any("cohort_year" in r["fields"] for r in logs["items"])
            assert all("name" not in r and "email" not in r for r in logs["items"])
            assert "New Student" not in str(logs) and "Math" not in str(logs)
            class FakeAI:
                engine=SimpleNamespace(mock_mode=True)
                def socratic_chat(self,payload):
                    return SimpleNamespace(ai_metadata=SimpleNamespace(provider="mock",prompt_truncated=True,extra={"secret":"DO_NOT_STORE"}),reply="DO_NOT_STORE")
                def grade_submission(self,payload):
                    raise RuntimeError("DO_NOT_STORE")
            ai = FakeAI()
            await ai_service.call_ai(ai.socratic_chat, {"prompt":"DO_NOT_STORE"})
            with pytest.raises(AIServiceError):
                await ai_service.call_ai(ai.grade_submission, {"prompt":"DO_NOT_STORE"})
            metrics = (await client.get("/admin/ai-metrics",headers=active)).json()
            assert len(metrics["groups"])==2
            assert sum(r["calls"] for r in metrics["groups"])==2
            assert sum(r["errors"] for r in metrics["groups"])==1
            assert sum(r["mock_calls"] for r in metrics["groups"])==2
            assert sum(r["truncated_calls"] for r in metrics["groups"])==1
            async with sessions() as db:
                rows=(await db.scalars(select(AIOperation))).all()
                assert "DO_NOT_STORE" not in str([r.__dict__ for r in rows])
                assert (await db.scalars(select(AuditEvent))).first() is not None
    finally:
        app.dependency_overrides.pop(get_db,None)
        await engine.dispose()
