"""Failure/concurrency/privacy checks against isolated PostgreSQL, using in-process HTTP."""
import asyncio
import datetime as dt
import uuid
import httpx
import pytest
from sqlalchemy import update
# This fixture module establishes isolated DATABASE_URL/SECRET_KEY before importing the app.
from test_ai_transactions import app, engine
from backend.database import AsyncSessionLocal
from backend.models.chat import ChatTurn, ChatMessage
from backend.models.enums import SenderType
from backend.models.submissions import Submission
from backend.services import chat_service
from backend.services.exceptions import AIServiceError
from ai_tutor.models import StudentChatResponse


@pytest.mark.asyncio
async def test_tutor_failure_retry_concurrency_and_context_privacy(monkeypatch):
    tag = uuid.uuid4().hex[:10]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {}
        for role in ("student", "professor"):
            body = dict(name=role, email=f"chat-{role}-{tag}@example.com", password="test-password-123",
                        role=role, staff_role=role, department="CS", student_number=tag, cohort_year=2027, major="CS")
            assert (await client.post("/auth/register", json=body)).status_code == 201
            login = await client.post("/auth/login", json={"email": body["email"], "password": body["password"]})
            headers[role] = {"Authorization": "Bearer " + login.json()["access_token"]}
        task_response = await client.post("/tasks/", headers=headers["professor"], json={
            "type": "assignment", "title": "Safe tutoring", "description": "PUBLIC_TASK_CONTEXT",
            "due_date": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat(),
            "target_cohort_year": 2027})
        task = task_response.json()["id"]
        rubric = (await client.post(f"/tasks/{task}/rubrics/create", headers=headers["professor"], json={
            "criteria": [{"name": "Public criterion", "max_points": 20}]})).json()["rubric_id"]
        await client.patch(f"/tasks/{task}/rubrics/status?rubric_id={rubric}", headers=headers["professor"], json={"status": "accepted"})
        submission = (await client.post("/submissions/", headers=headers["student"], json={
            "task_id": task, "submission_text": "OWN_EXPLANATION"})).json()["submission_id"]
        async with AsyncSessionLocal() as db:
            await db.execute(update(Submission).where(Submission.id == submission).values(feedback="PRIVATE_FEEDBACK_SENTINEL"))
            await db.commit()
        await client.post(f"/tasks/{task}/rubrics/create", headers=headers["professor"], json={
            "criteria": [{"name": "PRIVATE_DRAFT_SENTINEL", "max_points": 50}]})
        session = (await client.post(f"/tasks/{task}/chat-sessions", headers=headers["student"], json={
            "request_id": str(uuid.uuid4()), "submission_id": submission})).json()["id"]
        body = {"request_id": str(uuid.uuid4()), "content": "Please help me think"}
        seen = []
        async def failing(function, payload, **kwargs):
            seen.append(payload)
            assert "PUBLIC_TASK_CONTEXT" in payload.reference_text
            assert "OWN_EXPLANATION" in payload.reference_text
            assert "PRIVATE_FEEDBACK_SENTINEL" not in payload.reference_text
            assert "PRIVATE_DRAFT_SENTINEL" not in payload.reference_text
            raise AIServiceError("Private diagnostics")
        monkeypatch.setattr(chat_service, "call_ai", failing)
        response = await client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json=body)
        assert response.status_code == 503 and "Private diagnostics" not in response.text
        turns = (await client.get(f"/chat-sessions/{session}/messages", headers=headers["student"])).json()["items"]
        assert len(turns) == 1 and turns[0]["status"] == "failed" and turns[0]["retryable"]
        # A duplicate POST without explicit retry never re-runs a failed call.
        response = await client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json=body)
        assert response.status_code == 200 and len(seen) == 1
        # Simulate process interruption: an expired pending lease must be recoverable.
        async with AsyncSessionLocal() as db:
            await db.execute(update(ChatTurn).where(ChatTurn.id == turns[0]["id"]).values(
                status="pending", lease_until=dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=1)))
            await db.commit()
        started, finish = asyncio.Event(), asyncio.Event()
        async def delayed(function, payload, **kwargs):
            assert payload.chat_history == []  # Failed message is not a fake completed turn.
            started.set()
            await finish.wait()
            return StudentChatResponse(reply="What do you already know?")
        monkeypatch.setattr(chat_service, "call_ai", delayed)
        retry = asyncio.create_task(client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json={**body, "retry": True}))
        try:
            await asyncio.wait_for(started.wait(), 10)
            raced = await client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json={
                "request_id": str(uuid.uuid4()), "content": "A second request"})
            assert raced.status_code == 409 and raced.json()["code"] == "chat_busy"
        finally:
            finish.set()
        response = await retry
        assert response.status_code == 200, response.text
        completed = (await client.get(f"/chat-sessions/{session}/messages", headers=headers["student"])).json()["items"]
        assert len(completed) == 1 and completed[0]["reply"] == "What do you already know?"
        assert completed[0]["status"] == "completed"
        async with AsyncSessionLocal() as db:
            db.add_all([
                ChatMessage(session_id=session, sender_type=SenderType.user, content="LEGACY_QUESTION"),
                ChatMessage(session_id=session, sender_type=SenderType.assistant, content="LEGACY_REPLY"),
                ChatMessage(session_id=session, sender_type=SenderType.system, content="PRIVATE_SYSTEM_SENTINEL"),
            ])
            await db.commit()
        legacy = await client.get(f"/chat-sessions/{session}/legacy-messages", headers=headers["student"])
        assert legacy.status_code == 200
        assert [m["content"] for m in legacy.json()["items"]] == ["LEGACY_QUESTION", "LEGACY_REPLY"]
        assert (await client.get(f"/chat-sessions/{session}/legacy-messages", headers=headers["professor"])).status_code == 403
        async def inspect_legacy(function, payload, **kwargs):
            history = [m.content for m in payload.chat_history]
            assert "LEGACY_QUESTION" in history and "LEGACY_REPLY" in history
            assert "PRIVATE_SYSTEM_SENTINEL" not in history
            return StudentChatResponse(reply="Legacy-aware hint")
        monkeypatch.setattr(chat_service, "call_ai", inspect_legacy)
        legacy_reply = await client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json={
            "request_id": str(uuid.uuid4()), "content": "Continue our previous discussion"})
        assert legacy_reply.status_code == 200, legacy_reply.text
        monkeypatch.setattr(chat_service, "RATE", 1)
        limited = await client.post(f"/chat-sessions/{session}/messages", headers=headers["student"], json={
            "request_id": str(uuid.uuid4()), "content": "One more question"})
        assert limited.status_code == 429 and limited.json()["code"] == "chat_rate_limit"
    await engine.dispose()
