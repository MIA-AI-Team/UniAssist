import json

import pytest
from fastapi.testclient import TestClient

from app import app, engine


@pytest.fixture(autouse=True)
def mock_engine():
    """Run API tests without external LLM calls."""
    engine.mock_mode = True
    yield
    engine.mock_mode = True


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_RUBRIC = json.dumps([
    {
        "name": "Correctness",
        "description": "All operations work correctly",
        "max_points": 50.0,
        "sort_order": 1,
    },
    {
        "name": "Code Style",
        "description": "Clean readable code",
        "max_points": 50.0,
        "sort_order": 2,
    },
])


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Evaluation Assistant" in response.text


def test_suggest_rubric_with_text_override(client):
    response = client.post(
        "/api/suggest-rubric",
        data={
            "task_title": "Lab 1: Linked List",
            "task_type": "lab",
            "task_description": "Implement a doubly linked list.",
            "spec_text_override": "Students must implement insert, delete, and search.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["task_title"] == "Lab 1: Linked List"
    assert len(body["criteria"]) > 0
    assert body["total_max_points"] == sum(c["max_points"] for c in body["criteria"])


def test_refine_rubric_with_invalid_json(client):
    response = client.post(
        "/api/refine-rubric",
        data={
            "task_title": "Lab 1",
            "rubric_json": "not-valid-json",
            "staff_feedback": "Increase memory safety weight.",
        },
    )
    assert response.status_code == 400
    assert "Invalid previous rubric criteria format" in response.json()["detail"]


def test_refine_rubric_success(client):
    response = client.post(
        "/api/refine-rubric",
        data={
            "task_title": "Lab 1: Linked List",
            "task_type": "lab",
            "rubric_json": SAMPLE_RUBRIC,
            "staff_feedback": "Increase memory safety to 40 points.",
            "spec_text_override": "Implement insert, delete, and search.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["task_title"] == "Lab 1: Linked List"
    assert len(body["criteria"]) > 0


def test_grade_submission_missing_submission(client):
    response = client.post(
        "/api/grade-submission",
        data={
            "task_title": "Lab 1",
            "rubric_json": SAMPLE_RUBRIC,
            "spec_text_override": "Implement insert, delete, and search.",
        },
    )
    assert response.status_code == 400
    assert "upload a student submission" in response.json()["detail"].lower()


def test_grade_submission_missing_spec(client):
    response = client.post(
        "/api/grade-submission",
        data={
            "task_title": "Lab 1",
            "rubric_json": SAMPLE_RUBRIC,
            "submission_text_override": "def insert(node): pass",
        },
    )
    assert response.status_code == 400
    assert "specification" in response.json()["detail"].lower()


def test_grade_submission_with_text_override(client):
    response = client.post(
        "/api/grade-submission",
        data={
            "task_title": "Lab 1: Linked List",
            "task_type": "lab",
            "rubric_json": SAMPLE_RUBRIC,
            "submission_text_override": "def insert(node): pass",
            "spec_text_override": "Implement insert, delete, and search.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_possible_grade"] == 100.0
    assert len(body["criterion_evaluations"]) == 2
    assert 0 <= body["percentage"] <= 100.0
    assert body["ai_suggested_grade"] == sum(item["score_given"] for item in body["criterion_evaluations"])


def test_grade_submission_invalid_llm_response_returns_502(client, monkeypatch):
    engine.mock_mode = False

    def fake_call_llm(*args, **kwargs):
        return "this is not json"

    monkeypatch.setattr(engine, "_call_llm", fake_call_llm)

    response = client.post(
        "/api/grade-submission",
        data={
            "task_title": "Lab 1: Linked List",
            "task_type": "lab",
            "rubric_json": SAMPLE_RUBRIC,
            "submission_text_override": "def insert(node): pass",
            "spec_text_override": "Implement insert, delete, and search.",
        },
    )
    assert response.status_code == 502
    assert "invalid" in response.json()["detail"].lower()


def test_ai_metrics_endpoint(client):
    response = client.get("/api/ai/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "recent" in body


def test_ai_health_endpoint(client):
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_student_chat(client):
    response = client.post(
        "/api/student-chat",
        json={
            "task_title": "Lab 1: BST",
            "reference_text": "Implement a binary search tree.",
            "chat_history": [],
            "student_message": "Can you give me the direct solution code?",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert len(body["reply"]) > 0


def test_grade_all_submissions(client):
    # First submit a lab work
    client.post(
        "/api/submit-lab",
        data={
            "lab_id": "lab-1",
            "student_name": "John Doe",
            "student_id": "STU-100",
            "submission_text_override": "Measured tau = 10ms",
        },
    )
    # Trigger batch grade
    response = client.post("/api/grade-all-submissions/lab-1")
    assert response.status_code == 200
    body = response.json()
    assert body["graded_count"] >= 1
    assert body["total_submissions"] >= 1


def test_delete_lab(client):
    # Create a temporary lab
    create_res = client.post(
        "/api/create-lab",
        data={
            "title": "Temp Delete Test Lab",
            "lab_type": "experiment",
            "description": "To be deleted",
        },
    )
    assert create_res.status_code == 200
    lab_id = create_res.json()["id"]

    # Delete it
    del_res = client.delete(f"/api/delete-lab/{lab_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify 404
    get_res = client.get(f"/api/labs/{lab_id}")
    assert get_res.status_code == 404
