import pytest

from ai_metrics import AIMetricsCollector, metrics_collector
from ai_service import AIService, AnalyticsResponseError
from evaluator import ChatResponseError, RubricResponseError
from models import (
    CohortAnalyticsRequest,
    CohortCodeReviewSnapshot,
    CohortCriterionSnapshot,
    CohortGradeSnapshot,
    GradeSubmissionRequest,
    RubricCriteriaItem,
    RubricSuggestRequest,
    SocraticChatRequest,
)


@pytest.fixture
def service():
    svc = AIService()
    svc.engine.mock_mode = True
    return svc


def test_ai_service_suggest_rubric(service):
    response = service.suggest_rubric(
        RubricSuggestRequest(
            task_title="Lab 1",
            task_type="coding",
            reference_text="Implement a BST with insert and search.",
        )
    )
    assert response.task_title == "Lab 1"
    assert len(response.criteria) >= 1
    assert response.ai_metadata is not None
    assert response.ai_metadata.operation == "suggest_rubric"


def test_ai_service_grade_with_separate_grading_key(service):
    rubric = [
        RubricCriteriaItem(name="Correctness", description="Works", max_points=100.0, sort_order=1),
    ]
    response = service.grade_submission(
        GradeSubmissionRequest(
            task_title="Lab 2",
            task_type="coding",
            reference_text="Implement insert and search in a BST.",
            rubric_criteria=rubric,
            submission_text="class Node: pass",
            code_files={"main.py": "print('hi')\n"},
            grading_key="def insert(root, val): ... full TA solution ...",
        )
    )
    assert response.total_possible_grade == 100.0
    assert response.ai_metadata is not None
    assert response.ai_metadata.operation == "grade_submission"


def test_ai_service_rubric_invalid_llm_raises(monkeypatch):
    svc = AIService()
    svc.engine.mock_mode = False
    monkeypatch.setattr(svc.engine, "_call_llm", lambda *a, **k: "not-json")

    with pytest.raises(RubricResponseError):
        svc.suggest_rubric(
            RubricSuggestRequest(
                task_title="Lab 1",
                reference_text="Spec text here.",
            )
        )


def test_ai_service_chat_invalid_llm_raises(monkeypatch):
    svc = AIService()
    svc.engine.mock_mode = False
    monkeypatch.setattr(svc.engine, "_call_llm", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))

    with pytest.raises(ChatResponseError):
        svc.socratic_chat(
            SocraticChatRequest(
                student_message="Help me with this lab",
                reference_text="BST lab spec",
            )
        )


def test_ai_service_cohort_analytics_mock(service):
    response = service.analyze_cohort_patterns(
        CohortAnalyticsRequest(
            task_title="Lab 3: Recursion",
            task_type="coding",
            rubric_criteria_names=["Correctness", "Base cases"],
            grades=[
                CohortGradeSnapshot(grade=40, max_grade=100, feedback="Missed base case handling."),
                CohortGradeSnapshot(grade=55, max_grade=100, feedback="Recursive call incorrect."),
                CohortGradeSnapshot(grade=70, max_grade=100, feedback="Mostly correct with minor bugs."),
                CohortGradeSnapshot(grade=30, max_grade=100, feedback="No base case; stack overflow risk."),
            ],
            code_reviews=[
                CohortCodeReviewSnapshot(
                    severity="critical",
                    finding="Missing recursion base case",
                    file_path="solution.py",
                    count=6,
                ),
                CohortCodeReviewSnapshot(
                    severity="warning",
                    finding="Inefficient repeated recomputation",
                    file_path="solution.py",
                    count=3,
                ),
            ],
            criterion_stats=[
                CohortCriterionSnapshot(
                    criterion_name="Base cases",
                    average_score=8,
                    max_points=25,
                    low_score_count=5,
                ),
            ],
        )
    )
    assert response.student_count == 4
    assert response.task_title == "Lab 3: Recursion"
    assert response.summary
    assert response.common_issues
    assert response.teaching_focus
    assert response.ai_metadata is not None
    assert response.ai_metadata.operation == "analyze_cohort_patterns"


def test_ai_service_cohort_analytics_requires_data(service):
    with pytest.raises(ValueError, match="requires at least one"):
        service.analyze_cohort_patterns(
            CohortAnalyticsRequest(task_title="Empty Task")
        )


def test_ai_service_cohort_analytics_small_cohort_warning(service):
    response = service.analyze_cohort_patterns(
        CohortAnalyticsRequest(
            task_title="Tiny cohort",
            grades=[
                CohortGradeSnapshot(grade=80, max_grade=100, feedback="ok"),
            ],
        )
    )
    assert response.student_count == 1
    assert any("below" in w.lower() for w in response.warnings)


def test_ai_service_cohort_analytics_invalid_llm_raises(monkeypatch):
    svc = AIService()
    svc.engine.mock_mode = False
    monkeypatch.setattr(svc.engine, "_call_llm", lambda *a, **k: "not-json")

    with pytest.raises(AnalyticsResponseError):
        svc.analyze_cohort_patterns(
            CohortAnalyticsRequest(
                task_title="Lab X",
                grades=[
                    CohortGradeSnapshot(grade=50, max_grade=100, feedback="weak"),
                    CohortGradeSnapshot(grade=60, max_grade=100, feedback="ok"),
                    CohortGradeSnapshot(grade=40, max_grade=100, feedback="fail"),
                ],
            )
        )


def test_metrics_collector_summary():
    collector = AIMetricsCollector()
    with collector.track("test_op") as record:
        record.provider = "groq"
        record.model_used = "test-model"
        record.parse_success = True

    summary = collector.summary()
    assert summary["total_calls"] == 1
    assert summary["by_operation"]["test_op"] == 1


def test_metrics_collector_shared_instance():
    with metrics_collector.track("shared_test") as record:
        record.parse_success = True
    assert metrics_collector.summary()["total_calls"] >= 1
