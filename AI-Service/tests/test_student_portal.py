import pytest
from fastapi.testclient import TestClient
from app import app, SUBMISSIONS_DB
from ai_tutor.models.lab import LabSubmission
from ai_tutor.models.grading import SubmissionGradingResponse

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_mock_data():
    # Setup mock data for tests
    mock_sub = LabSubmission(
        id="sub-test-123",
        lab_id="lab-1",
        student_name="Test Student",
        student_id="STU-999",
        submission_text="Test",
        code_files={},
        submitted_at="2026-09-04",
        status="graded",
        grade_result=SubmissionGradingResponse(
            ai_suggested_grade=80.0,
            total_possible_grade=100.0,
            percentage=80.0,
            summary_feedback="Good job",
            criterion_evaluations=[
                {"criterion_name": "Test", "score_given": 80, "max_points": 100, "reasoning": "Ok"}
            ],
            code_reviews=[],
            warnings=[]
        )
    )
    SUBMISSIONS_DB.append(mock_sub)
    yield
    SUBMISSIONS_DB.pop()

def test_update_feedback():
    response = client.post("/api/submission/sub-test-123/update-feedback", json={
        "score": 95.0,
        "summary_feedback": "Excellent job!",
        "professor_notes": "Well done, keep it up."
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify DB updated
    updated_sub = next(s for s in SUBMISSIONS_DB if s.id == "sub-test-123")
    assert updated_sub.grade_result.percentage == 95.0
    assert updated_sub.grade_result.summary_feedback == "Excellent job!"
    assert updated_sub.grade_result.professor_notes == "Well done, keep it up."

def test_student_feedback_shields_rubric():
    # First update to add professor notes so we can test it
    client.post("/api/submission/sub-test-123/update-feedback", json={
        "score": 95.0,
        "summary_feedback": "Excellent job!",
        "professor_notes": "Well done, keep it up."
    })
    
    response = client.get("/api/student-feedback/STU-999")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Verify rubric is shielded
    grade_result = data[-1]["grade_result"]
    assert grade_result["criterion_evaluations"] == []
    assert grade_result["code_reviews"] == []
    
    # Verify professor notes are present
    assert grade_result["professor_notes"] == "Well done, keep it up."
