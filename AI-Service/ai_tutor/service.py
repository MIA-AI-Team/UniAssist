"""Stable AI service facade for backend team integration."""

from __future__ import annotations

from typing import List, Optional

from ai_tutor.config import Config
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
    ChatMessage,
    ChatSessionScope,
    CohortAnalyticsRequest,
    CohortAnalyticsResponse,
    GradeSubmissionRequest,
    LabAssistantChatRequest,
    LabChatResponse,
    PersistedChatMessage,
    RubricRefineRequest,
    RubricSuggestRequest,
    RubricSuggestionResponse,
    SocraticChatRequest,
    StudentChatResponse,
    SubmissionGradingResponse,
    chat_history_from_persisted,
    trim_chat_history,
)
from ai_tutor.models.chat_session import scope_as_metadata


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

    def build_chat_history(
        self,
        persisted_messages: List[PersistedChatMessage],
        *,
        max_messages: Optional[int] = None,
    ) -> List[ChatMessage]:
        """
        Convert CHAT_MESSAGES rows into AI chat_history (continue-later).

        Backend: load messages for CHAT_SESSIONS.id ordered by created_at ASC.
        """
        limit = Config.MAX_CHAT_HISTORY_MESSAGES if max_messages is None else max_messages
        return chat_history_from_persisted(persisted_messages, max_messages=limit)

    def socratic_chat(self, request: SocraticChatRequest) -> StudentChatResponse:
        history = self._resolve_chat_history(request.chat_history, request.persisted_messages)
        response = self._engine.socratic_tutor_chat(
            reference_text=request.reference_text,
            chat_history=history,
            student_message=request.student_message,
            task_title=request.task_title,
            response_language=request.response_language,
        )
        return self._attach_session(response, request.session, request.request_metadata)

    def lab_assistant_chat(self, request: LabAssistantChatRequest) -> LabChatResponse:
        history = self._resolve_chat_history(request.chat_history, request.persisted_messages)
        response = self._engine.lab_assistant_chat(
            lab_title=request.lab_title,
            lab_type=request.lab_type,
            steps_and_theory=request.steps_and_theory,
            model_answers=request.model_answers,
            chat_history=history,
            student_message=request.student_message,
            response_language=request.response_language,
        )
        return self._attach_session(response, request.session, request.request_metadata)

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
            response_language=request.response_language,
        )

    def _resolve_chat_history(
        self,
        chat_history: List[ChatMessage],
        persisted_messages: List[PersistedChatMessage],
    ) -> List[ChatMessage]:
        if chat_history:
            return trim_chat_history(chat_history, Config.MAX_CHAT_HISTORY_MESSAGES)
        if persisted_messages:
            return chat_history_from_persisted(
                persisted_messages,
                max_messages=Config.MAX_CHAT_HISTORY_MESSAGES,
            )
        return []

    def _attach_session(self, response, session: Optional[ChatSessionScope], request_metadata: Optional[dict]):
        if session is not None:
            response.session_id = session.session_id
        if response.ai_metadata is not None:
            extra = dict(response.ai_metadata.extra or {})
            extra.update(scope_as_metadata(session))
            if request_metadata:
                extra.update(request_metadata)
            response.ai_metadata.extra = extra or None
        return response


__all__ = [
    "AIService",
    "GradingResponseError",
    "RubricResponseError",
    "ChatResponseError",
    "AnalyticsResponseError",
]
