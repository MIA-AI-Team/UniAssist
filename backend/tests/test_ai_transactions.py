"""Failure/concurrency checks against real PostgreSQL using in-process HTTP."""
import asyncio
import datetime as dt
import os
from pathlib import Path
import sys
import uuid

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "AI-Service")]
# Explicitly use only the isolated verification database, never a user's .env.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://verify:verify-local-only@localhost:15432/verify"
os.environ["SECRET_KEY"] = "isolated-asgi-verification-secret"
os.environ["MOCK_MODE"] = "true"
os.environ["UPLOAD_DIR"] = str(ROOT / "backend" / "uploads" / "verification")

from backend.main import app
from backend.database import engine
from backend.services import grading_service
from backend.services.exceptions import AIServiceError, AIRubricError


@pytest.mark.asyncio
async def test_ai_failure_rolls_back_and_resubmission_cannot_race_evaluation(monkeypatch):
    tag = uuid.uuid4().hex[:10]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {}
        for role in ("student", "professor"):
            body = dict(name=role, email=f"{role}-{tag}@example.com", password="test-password-123",
                        role=role, staff_role=role, department="CS", student_number=tag, cohort_year=2027, major="CS")
            assert (await client.post("/auth/register", json=body)).status_code == 201
            login = await client.post("/auth/login", json={"email": body["email"], "password": body["password"]})
            headers[role] = {"Authorization": "Bearer " + login.json()["access_token"]}
        task = (await client.post("/tasks/", headers=headers["professor"], json={
            "type": "assignment", "title": "Transaction checks", "description": "Reference: explain complexity.",
            "due_date": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat(),
            "target_cohort_year": 2027, "allowed_file_types": ["py"]})).json()["id"]
        rubric = (await client.post(f"/tasks/{task}/rubrics/create", headers=headers["professor"], json={
            "criteria": [{"name": "Reasoning", "description": "Clear reasoning", "max_points": 20}]})).json()["rubric_id"]
        await client.patch(f"/tasks/{task}/rubrics/status?rubric_id={rubric}", headers=headers["professor"], json={"status": "accepted"})
        upload = await client.post("/files/upload", headers=headers["student"], data={"purpose": "submission", "task_id": task},
                                   files={"file": ("analysis.py", b"def search(items):\n    return items[0]\n")})
        assert upload.status_code == 201, upload.text
        response = await client.post("/submissions/", headers=headers["student"], json={
            "task_id": task, "submission_text": "My separate explanation", "file_id": upload.json()["file_id"]})
        assert response.status_code == 201, response.text
        sid = response.json()["submission_id"]
        original_call = grading_service.call_ai

        for exception, status, code in ((AIServiceError, 503, "ai_unavailable"), (AIRubricError, 502, "ai_invalid_response")):
            async def failing(*args):
                raise exception("Private provider diagnostics must not leak")
            monkeypatch.setattr(grading_service, "call_ai", failing)
            result = await client.post(f"/submissions/{sid}/grade", headers=headers["professor"])
            assert result.status_code == status and result.json()["code"] == code
            assert "Private provider" not in result.text
            detail = (await client.get(f"/submissions/{sid}", headers=headers["professor"])).json()
            assert detail["status"] == "pending" and detail["ai_suggested_grade"] is None

        started, finish = asyncio.Event(), asyncio.Event()
        async def delayed(function, payload):
            assert "My separate explanation" in payload.submission_text
            assert payload.code_files and "Reference:" in payload.reference_text
            assert "My separate explanation" not in payload.reference_text
            started.set()
            await finish.wait()
            return await original_call(function, payload)
        monkeypatch.setattr(grading_service, "call_ai", delayed)
        grading = asyncio.create_task(client.post(f"/submissions/{sid}/grade", headers=headers["professor"]))
        await asyncio.wait_for(started.wait(), 10)
        raced = await client.post("/submissions/", headers=headers["student"], json={"task_id": task, "submission_text": "New attempt"})
        assert raced.status_code == 409 and raced.json()["code"] == "review_in_progress"
        finish.set()
        result = await grading
        assert result.status_code == 200, result.text
        detail = (await client.get(f"/submissions/{sid}", headers=headers["professor"])).json()
        assert detail["code_reviews"] and detail["is_mock"] is True
        history = (await client.get(f"/submissions/my/{task}", headers=headers["student"])).json()
        assert len(history) == 1 and history[0]["is_latest"]
    await engine.dispose()
