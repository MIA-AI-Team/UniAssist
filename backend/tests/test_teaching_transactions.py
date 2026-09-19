"""Boundary capture and transaction tests against the isolated PostgreSQL database."""
import asyncio
import datetime as dt
import uuid
import httpx
import pytest
from sqlalchemy import select, update, func
from test_ai_transactions import app, engine
from backend.database import AsyncSessionLocal
from backend.models.submissions import Submission
from backend.models.repository import CodeReview
from backend.models.enums import SubmissionStatus, ReviewType, Severity
from backend.models.teaching import TeachingReport
from backend.services import grading_service, rubric_service, chat_service, teaching_service
from backend.services.exceptions import AIServiceError
from ai_tutor.models import CohortAnalyticsResponse


@pytest.mark.asyncio
async def test_private_guidance_boundary_and_aggregate_report_fencing(monkeypatch):
    tag = uuid.uuid4().hex[:10]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {}
        for name in ("professor", "student0", "student1", "student2"):
            role = "professor" if name == "professor" else "student"
            body = dict(name="IDENTITY_SENTINEL", email=f"{name}-{tag}@example.com", password="testing-password",
                        role=role, staff_role=role, department="CS", student_number=name+tag, cohort_year=2027, major="CS")
            assert (await client.post("/auth/register", json=body)).status_code == 201
            token = (await client.post("/auth/login", json={"email": body["email"], "password": body["password"]})).json()["access_token"]
            headers[name] = {"Authorization": "Bearer " + token}
        staff = headers["professor"]
        task = (await client.post("/tasks/", headers=staff, json={"type": "assignment", "title": "TITLE_SENTINEL",
            "description": "PUBLIC_CONTEXT", "due_date": (dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1)).isoformat(),
            "target_cohort_year": 2027})).json()["id"]
        rubric = (await client.post(f"/tasks/{task}/rubrics/create", headers=staff,
            json={"criteria": [{"name": "AUTHORED_CRITERION_SENTINEL", "max_points": 20}]})).json()["rubric_id"]
        await client.patch(f"/tasks/{task}/rubrics/status?rubric_id={rubric}", headers=staff, json={"status": "accepted"})
        guidance = (await client.post(f"/tasks/{task}/grading-guidance", headers=staff,
            json={"request_id": str(uuid.uuid4()), "content": "PRIVATE_KEY_SENTINEL"})).json()["id"]
        original_grade = grading_service.call_ai
        async def inspect_grade(function, payload):
            assert payload.grading_key == "PRIVATE_KEY_SENTINEL"
            return await original_grade(function, payload)
        monkeypatch.setattr(grading_service, "call_ai", inspect_grade)
        ids = []
        for index in range(3):
            sid = (await client.post("/submissions/", headers=headers[f"student{index}"],
                json={"task_id": task, "submission_text": "WORK_SENTINEL"})).json()["submission_id"]
            ids.append(sid)
            result = await client.post(f"/submissions/{sid}/grade", headers=staff)
            assert result.status_code == 200, result.text
            await client.patch(f"/submissions/{sid}/confirm", headers=staff, json={"final_grade": 10 + index})
        async def public_only(function, payload, **kwargs):
            assert "PRIVATE_KEY_SENTINEL" not in payload.model_dump_json()
            return await original_grade(function, payload, **kwargs)
        monkeypatch.setattr(chat_service, "call_ai", public_only)
        monkeypatch.setattr(rubric_service, "call_ai", public_only)
        session = (await client.post(f"/tasks/{task}/chat-sessions", headers=headers["student0"],
            json={"request_id": str(uuid.uuid4())})).json()["id"]
        assert (await client.post(f"/chat-sessions/{session}/messages", headers=headers["student0"],
            json={"request_id": str(uuid.uuid4()), "content": "A hint please"})).status_code == 200
        assert (await client.post(f"/tasks/{task}/rubrics/suggest", headers=staff)).status_code == 201
        async with AsyncSessionLocal() as db:
            rows = list((await db.scalars(select(Submission).where(Submission.id.in_(ids)))).all())
            for row in rows:
                assert row.grading_guidance_id == guidance
                row.feedback = "FEEDBACK_SENTINEL"
                db.add(CodeReview(submission_id=row.id, review_type=ReviewType.ai_code_review,
                    severity=Severity.warning, finding="FINDING_SENTINEL", file_path="FILENAME_SENTINEL", line_number=1))
            # Legacy newer unconfirmed work must not remove the last confirmed result from analytics.
            rows[0].is_latest = False
            db.add(Submission(task_id=task, student_id=rows[0].student_id, rubric_id=rubric,
                attempt_number=2, is_latest=True, submission_text="LATER_WORK_SENTINEL", status=SubmissionStatus.pending))
            await db.commit()
        path = f"/tasks/{task}/analytics"
        snapshot = (await client.get(path, headers=staff)).json()
        assert snapshot["released_count"] == 3 and snapshot["groups"][0]["average_percentage"] == 55
        body = {"request_id": str(uuid.uuid4()), "rubric_id": rubric, "language": "ar"}
        def inspect(payload):
            assert "SENTINEL" not in payload.model_dump_json()
            assert len(payload.grades) == 3 and all(g.feedback == "" for g in payload.grades)
            assert payload.code_reviews[0].count == 3 and payload.code_reviews[0].file_path is None
            assert payload.response_language == "ar"
        async def failing(function, payload):
            inspect(payload)
            raise AIServiceError("PRIVATE_PROVIDER_DIAGNOSTIC")
        monkeypatch.setattr(teaching_service, "call_ai", failing)
        failed = await client.post(path + "/reports", headers=staff, json=body)
        assert failed.status_code == 503 and "PRIVATE_PROVIDER_DIAGNOSTIC" not in failed.text
        assert (await client.get(path + "/reports", headers=staff)).json()["items"] == []
        entered, finish = asyncio.Event(), asyncio.Event()
        async def delayed(function, payload):
            inspect(payload)
            entered.set()
            await finish.wait()
            return CohortAnalyticsResponse(task_title="Safe", student_count=3, summary="اقتراح تجريبي آمن")
        monkeypatch.setattr(teaching_service, "call_ai", delayed)
        running = asyncio.create_task(client.post(path + "/reports", headers=staff, json=body))
        try:
            await asyncio.wait_for(entered.wait(), 10)
            competing = await client.post(path + "/reports", headers=staff, json=body)
            assert competing.status_code == 409 and competing.json()["code"] == "analytics_busy"
            async with AsyncSessionLocal() as db:
                await db.execute(update(Submission).where(Submission.id == ids[2]).values(final_grade=15))
                await db.commit()
        finally:
            finish.set()
        response = await running
        assert response.status_code == 201, response.text
        assert response.json()["stale"] and response.json()["input_snapshot"]["average_percentage"] == 55
        replay = await client.post(path + "/reports", headers=staff, json=body)
        assert replay.json()["id"] == response.json()["id"]
        async with AsyncSessionLocal() as db:
            assert await db.scalar(select(func.count()).select_from(TeachingReport).where(TeachingReport.task_id == task)) == 1
    await engine.dispose()
