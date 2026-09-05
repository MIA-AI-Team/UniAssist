"""Stable AI service facade for backend team integration."""

from __future__ import annotations

from typing import Optional

from ai_tutor.metrics import metrics_collector
from ai_tutor.engine import (
    AIEvaluationEngine,
    AnalyticsResponseError,
    ChatResponseError,
    GradingResponseError,
    RubricResponseError,
)
from ai_tutor.parsers import prepare_submission_for_grading
from ai_tutor.models import (
    CohortAnalyticsRequest,
    CohortAnalyticsResponse,
    GradeSubmissionRequest,
    LabAssistantChatRequest,
    LabChatResponse,
    RubricRefineRequest,
    RubricSuggestRequest,
    RubricSuggestionResponse,
    SocraticChatRequest,
    StudentChatResponse,
    SubmissionGradingResponse,
)


class AIService:
    """
    Single entry point for all AI capabilities.
    Backend team should call this layer — not FastAPI routes or file upload logic.
    """

    def __init__(self, engine: Optional[AIEvaluationEngine] = None):
        self._engine = engine or AIEvaluationEngine()

    @property
    def engine(self) -> AIEvaluationEngine:
        return self._engine

    def metrics_summary(self) -> dict:
        return metrics_collector.summary()

    def recent_metrics(self, limit: int = 50) -> list:
        return [r.__dict__ for r in metrics_collector.recent(limit)]

    def suggest_rubric(self, request: RubricSuggestRequest) -> RubricSuggestionResponse:
        return self._engine.suggest_rubric(
            task_title=request.task_title,
            task_type=request.task_type,
            task_description=request.task_description,
            reference_text=request.reference_text,
        )

    def refine_rubric(self, request: RubricRefineRequest) -> RubricSuggestionResponse:
        return self._engine.refine_rubric(
            task_title=request.task_title,
            task_type=request.task_type,
            task_description=request.task_description,
            reference_text=request.reference_text,
            previous_criteria=request.previous_criteria,
            staff_feedback=request.staff_feedback,
        )

    def grade_submission(self, request: GradeSubmissionRequest) -> SubmissionGradingResponse:
        submission_text, code_files, prep_warnings = prepare_submission_for_grading(
            submission_text=request.submission_text,
            code_files=request.code_files,
        )
        return self._engine.grade_submission(
            task_title=request.task_title,
            task_type=request.task_type,
            reference_text=request.reference_text,
            rubric_criteria=request.rubric_criteria,
            submission_text=submission_text,
            code_files=code_files,
            grading_key=request.grading_key,
            prep_warnings=prep_warnings,
        )

    def socratic_chat(self, request: SocraticChatRequest) -> StudentChatResponse:
        return self._engine.socratic_tutor_chat(
            reference_text=request.reference_text,
            chat_history=request.chat_history,
            student_message=request.student_message,
            task_title=request.task_title,
        )

    def lab_assistant_chat(self, request: LabAssistantChatRequest) -> LabChatResponse:
        return self._engine.lab_assistant_chat(
            lab_title=request.lab_title,
            lab_type=request.lab_type,
            steps_and_theory=request.steps_and_theory,
            model_answers=request.model_answers,
            chat_history=request.chat_history,
            student_message=request.student_message,
        )

    def analyze_cohort_patterns(self, request: CohortAnalyticsRequest) -> CohortAnalyticsResponse:
        """Staff-facing cohort insights. Backend aggregates DB rows and anonymizes before calling."""
        return self._engine.analyze_cohort_patterns(
            task_title=request.task_title,
            task_type=request.task_type,
            task_description=request.task_description,
            rubric_criteria_names=request.rubric_criteria_names,
            grades=request.grades,
            code_reviews=request.code_reviews,
            criterion_stats=request.criterion_stats,
        )


__all__ = [
    "AIService",
    "GradingResponseError",
    "RubricResponseError",
    "ChatResponseError",
    "AnalyticsResponseError",
]
