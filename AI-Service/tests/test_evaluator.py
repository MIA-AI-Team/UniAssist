import json
import sys
import pytest
from evaluator import AIEvaluationEngine, GradingResponseError
from models import (
    CriterionEvaluation,
    RubricCriteriaItem,
    RubricSuggestionResponse,
    SubmissionGradingResponse,
)

# Ensure stdout handles UTF-8 characters on Windows consoles
sys.stdout.reconfigure(encoding='utf-8')


def test_suggest_rubric_mock():
    """Verify suggest_rubric execution in mock/fallback mode."""
    engine = AIEvaluationEngine()
    engine.mock_mode = True

    task_title = "Lab 1: Linked List Implementation"
    task_type = "lab"
    task_description = "Implement a doubly linked list in C++ with memory management."
    reference_text = "Lab specification: Implement insert, delete, search, and destructor. Ensure no memory leaks using valgrind."

    response = engine.suggest_rubric(
        task_title=task_title,
        task_type=task_type,
        task_description=task_description,
        reference_text=reference_text,
    )

    assert isinstance(response, RubricSuggestionResponse)
    assert response.task_title == task_title
    assert len(response.criteria) > 0
    assert response.total_max_points == sum(c.max_points for c in response.criteria)
    assert response.rationale != ""


def test_grade_submission_mock():
    """Verify grade_submission execution in mock/fallback mode."""
    engine = AIEvaluationEngine()
    engine.mock_mode = True

    task_title = "Lab 1: Linked List Implementation"
    task_type = "lab"
    reference_text = "Lab specification: Implement insert, delete, search, and destructor."

    rubric_criteria = [
        RubricCriteriaItem(name="Correctness", description="All operations work correctly", max_points=50.0, sort_order=1),
        RubricCriteriaItem(name="Memory Management", description="No memory leaks", max_points=30.0, sort_order=2),
        RubricCriteriaItem(name="Code Style", description="Clean code with comments", max_points=20.0, sort_order=3),
    ]

    submission_text = "Student Submission: Attached files main.cpp and LinkedList.cpp."
    code_files = {
        "LinkedList.cpp": "void deleteNode(Node* head, int val) { /* deletion logic */ }"
    }

    response = engine.grade_submission(
        task_title=task_title,
        task_type=task_type,
        reference_text=reference_text,
        rubric_criteria=rubric_criteria,
        submission_text=submission_text,
        code_files=code_files,
    )

    assert isinstance(response, SubmissionGradingResponse)
    assert response.ai_suggested_grade >= 0
    assert response.total_possible_grade == 100.0
    assert 0 <= response.percentage <= 100.0
    assert len(response.criterion_evaluations) == len(rubric_criteria)
    assert isinstance(response.summary_feedback, str)
    assert len(response.code_reviews) == 1


def test_grade_submission_requires_spec():
    engine = AIEvaluationEngine()
    engine.mock_mode = True
    rubric = [RubricCriteriaItem(name="Correctness", description="Works", max_points=100.0, sort_order=1)]

    with pytest.raises(ValueError, match="specification is required"):
        engine.grade_submission(
            task_title="Lab 1",
            task_type="lab",
            reference_text="",
            rubric_criteria=rubric,
            submission_text="print('hi')",
        )


def test_grade_submission_requires_submission_content():
    engine = AIEvaluationEngine()
    engine.mock_mode = True
    rubric = [RubricCriteriaItem(name="Correctness", description="Works", max_points=100.0, sort_order=1)]

    with pytest.raises(ValueError, match="submission is empty"):
        engine.grade_submission(
            task_title="Lab 1",
            task_type="lab",
            reference_text="Implement a queue.",
            rubric_criteria=rubric,
            submission_text="   ",
            code_files=None,
        )


def test_normalize_grading_response_recomputes_total():
    engine = AIEvaluationEngine()
    rubric = [
        RubricCriteriaItem(name="Correctness", description="Works", max_points=50.0, sort_order=1),
        RubricCriteriaItem(name="Style", description="Readable", max_points=50.0, sort_order=2),
    ]
    raw = SubmissionGradingResponse(
        ai_suggested_grade=999.0,
        total_possible_grade=10.0,
        percentage=99.0,
        summary_feedback="Test",
        criterion_evaluations=[
            CriterionEvaluation(criterion_name="Correctness", score_given=40.0, max_points=50.0, reasoning="Good"),
            CriterionEvaluation(criterion_name="Style", score_given=45.0, max_points=50.0, reasoning="Great"),
        ],
    )

    normalized = engine._normalize_grading_response(raw, rubric)

    assert normalized.ai_suggested_grade == 85.0
    assert normalized.total_possible_grade == 100.0
    assert normalized.percentage == 85.0


def test_normalize_grading_response_caps_scores_above_max():
    engine = AIEvaluationEngine()
    rubric = [RubricCriteriaItem(name="Correctness", description="Works", max_points=50.0, sort_order=1)]
    raw = SubmissionGradingResponse(
        ai_suggested_grade=80.0,
        total_possible_grade=50.0,
        percentage=80.0,
        summary_feedback="Test",
        criterion_evaluations=[
            CriterionEvaluation(criterion_name="Correctness", score_given=80.0, max_points=50.0, reasoning="Too high"),
        ],
    )

    normalized = engine._normalize_grading_response(raw, rubric)

    assert normalized.criterion_evaluations[0].score_given == 50.0
    assert normalized.ai_suggested_grade == 50.0
    assert normalized.percentage == 100.0
    assert any("adjusted" in warning.lower() for warning in normalized.warnings)


def test_grade_submission_raises_on_invalid_llm_response(monkeypatch):
    engine = AIEvaluationEngine()
    engine.mock_mode = False
    monkeypatch.setattr(engine, "_call_llm", lambda *args, **kwargs: "not-json")

    rubric = [RubricCriteriaItem(name="Correctness", description="Works", max_points=100.0, sort_order=1)]

    with pytest.raises(GradingResponseError):
        engine.grade_submission(
            task_title="Lab 1",
            task_type="lab",
            reference_text="Implement a queue.",
            rubric_criteria=rubric,
            submission_text="class Queue: pass",
        )


def test_mock_grade_submission_includes_code_reviews_only_with_code():
    engine = AIEvaluationEngine()
    engine.mock_mode = True
    rubric = [RubricCriteriaItem(name="Correctness", description="Works", max_points=100.0, sort_order=1)]

    without_code = engine.grade_submission(
        task_title="Lab 1",
        task_type="lab",
        reference_text="Implement a queue.",
        rubric_criteria=rubric,
        submission_text="Written answer only.",
    )
    with_code = engine.grade_submission(
        task_title="Lab 1",
        task_type="lab",
        reference_text="Implement a queue.",
        rubric_criteria=rubric,
        submission_text="Code submission.",
        code_files={"main.py": "print('hello')\n"},
    )

    assert without_code.code_reviews == []
    assert len(with_code.code_reviews) == 1


def test_normalize_rubric_response_fixes_total():
    engine = AIEvaluationEngine()
    response = RubricSuggestionResponse(
        task_title="Lab 1",
        criteria=[
            RubricCriteriaItem(name="A", description="d", max_points=30.0, sort_order=1),
            RubricCriteriaItem(name="B", description="d", max_points=70.0, sort_order=2),
        ],
        total_max_points=50.0,
        rationale="test",
    )
    normalized = engine._normalize_rubric_response(response)
    assert normalized.total_max_points == 100.0
    assert any("adjusted" in w.lower() for w in normalized.warnings)


def test_sanitize_lab_reply_blocks_leak_phrase():
    engine = AIEvaluationEngine()
    reply, sanitized = engine._sanitize_lab_reply(
        "Here is the complete solution: int main() { return 0; }",
        model_answers="int main() { return 0; }",
    )
    assert sanitized is True
    assert "cannot" in reply.lower()


def test_gemini_fallback_uses_secondary_model():
    """Primary Gemini failure should retry with GEMINI_FALLBACK_MODEL."""
    from config import Config

    engine = AIEvaluationEngine()
    engine.mock_mode = False
    engine._groq_client = None

    calls = []

    class FakeModels:
        @staticmethod
        def generate_content(*, model, contents, config):
            calls.append(model)
            if model == Config.GEMINI_MODEL:
                raise RuntimeError("primary unavailable")
            return type("Resp", (), {"text": '{"ok": true}'})()

    engine._gemini_client = type("FakeGeminiClient", (), {"models": FakeModels})()

    result = engine._call_gemini("system", "user", response_json=True)

    assert result == '{"ok": true}'
    assert calls == [Config.GEMINI_MODEL, Config.GEMINI_FALLBACK_MODEL]


def test_socratic_tutor_chat_mock():
    """Verify socratic_tutor_chat execution and guardrails in mock mode."""
    engine = AIEvaluationEngine()
    engine.mock_mode = True

    # 1. Test student asking for direct code
    response1 = engine.socratic_tutor_chat(
        reference_text="Implement a binary search tree in C++.",
        chat_history=[],
        student_message="Can you give me the direct solution code?",
        task_title="Lab 1: BST"
    )
    assert "cannot write the direct code" in response1.reply.lower() or "solve it step-by-step" in response1.reply.lower()

    # 2. Test student asking conceptual question
    response2 = engine.socratic_tutor_chat(
        reference_text="Implement a binary search tree in C++.",
        chat_history=[],
        student_message="How do I handle root node insertion?",
        task_title="Lab 1: BST"
    )
    assert len(response2.reply) > 0


def test_lab_assistant_chat_mock():
    """Verify lab_assistant_chat execution for experiment and coding labs."""
    engine = AIEvaluationEngine()
    engine.mock_mode = True

    # 1. Test Experiment Lab procedure routing
    exp_resp = engine.lab_assistant_chat(
        lab_title="Lab 1: RC Circuit Transient Dynamics",
        lab_type="experiment",
        steps_and_theory="Step 1: Wire resistor and capacitor. Step 2: Measure time constant tau on oscilloscope.",
        model_answers="tau = R * C = 10ms",
        chat_history=[],
        student_message="What is Step 1 in the procedure?"
    )
    assert exp_resp.detected_mode == "experiment_guide"
    assert "Step Guidance" in exp_resp.reply or "Circuit" in exp_resp.reply or "Step 2" in exp_resp.reply

    # 2. Test Coding Lab hint-only guardrail
    code_resp = engine.lab_assistant_chat(
        lab_title="Lab 2: BST Implementation",
        lab_type="coding",
        steps_and_theory="Implement insert(root, val) in BST.",
        model_answers="TreeNode* insert(TreeNode* root, int val) { ... }",
        chat_history=[],
        student_message="Give me the direct solution code"
    )
    assert code_resp.detected_mode == "coding_hint"
    assert "Hint Only Mode" in code_resp.reply or "cannot give direct solution code" in code_resp.reply.lower()


def run_sample_demo():
    """Demonstrate end-to-end evaluation flow with sample university lab data."""
    print("=" * 70)
    print("AI EVALUATION ENGINE SERVICE - LIVE DEMO RUN")
    print("=" * 70)

    engine = AIEvaluationEngine()

    # Step 1: Define Lab Specification
    task_title = "Lab 3: Thread-Safe Bounded Buffer Queue"
    task_type = "lab"
    task_description = "Implement a thread-safe bounded queue in C++ using mutexes and condition variables."
    reference_text = """
    Specification:
    Students must implement a ThreadSafeQueue<T> template class with a fixed capacity N.
    Methods required:
    1. push(T item): Blocks if queue is full.
    2. pop(): Blocks if queue is empty and returns the item.
    3. size(): Returns current element count.
    
    Constraints:
    - Use std::mutex and std::condition_variable.
    - Avoid deadlocks and race conditions.
    - Properly unlock mutexes in exception paths.
    """

    print(f"\n[1] Generating AI Rubric Suggestion for: '{task_title}'...")
    rubric_response = engine.suggest_rubric(
        task_title=task_title,
        task_type=task_type,
        task_description=task_description,
        reference_text=reference_text,
    )

    print(f"-> Rubric Created! Rationale: {rubric_response.rationale}\n")
    print("Rubric Criteria:")
    for c in rubric_response.criteria:
        print(f"  - [{c.sort_order}] {c.name} ({c.max_points} pts): {c.description}")
    print(f"  Total Max Points: {rubric_response.total_max_points}")

    # Step 2: Grade Student Submission
    submission_text = "Student Submission by Student #10492 for Thread-Safe Queue Lab."
    student_code = {
        "BoundedQueue.hpp": """
#include <mutex>
#include <condition_variable>
#include <queue>

template<typename T>
class BoundedQueue {
private:
    std::queue<T> q;
    size_t capacity;
    std::mutex mtx;
    std::condition_variable cv_full, cv_empty;

public:
    BoundedQueue(size_t cap) : capacity(cap) {}

    void push(T item) {
        std::unique_lock<std::mutex> lock(mtx);
        cv_full.wait(lock, [this]() { return q.size() < capacity; });
        q.push(item);
        cv_empty.notify_one();
    }

    T pop() {
        std::unique_lock<std::mutex> lock(mtx);
        cv_empty.wait(lock, [this]() { return !q.empty(); });
        T item = q.front();
        q.pop();
        cv_full.notify_one();
        return item;
    }
};
"""
    }

    print(f"\n[2] Grading Student Submission against generated Rubric...")
    grading_response = engine.grade_submission(
        task_title=task_title,
        task_type=task_type,
        reference_text=reference_text,
        rubric_criteria=rubric_response.criteria,
        submission_text=submission_text,
        code_files=student_code,
    )

    print("\n" + "=" * 70)
    print(f"EVALUATION RESULT: {grading_response.ai_suggested_grade} / {grading_response.total_possible_grade} ({grading_response.percentage}%)")
    print("=" * 70)
    print(f"Summary Feedback: {grading_response.summary_feedback}\n")

    print("Criterion Breakdown:")
    for eval_item in grading_response.criterion_evaluations:
        print(f"  - {eval_item.criterion_name}: {eval_item.score_given}/{eval_item.max_points} pts")
        print(f"    Reasoning: {eval_item.reasoning}")

    if grading_response.code_reviews:
        print("\nCode Review Findings:")
        for rev in grading_response.code_reviews:
            print(f"  - [{rev.severity.upper()}] {rev.file_path}:{rev.line_number or 'N/A'} - {rev.finding}")


if __name__ == "__main__":
    run_sample_demo()
