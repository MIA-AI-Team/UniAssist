"""Backward-compatible shim — use `from ai_tutor.engine import ...` in new code."""

from ai_tutor.engine import (
    AIEvaluationEngine,
    AnalyticsResponseError,
    ChatResponseError,
    GradingResponseError,
    RubricResponseError,
)

__all__ = [
    "AIEvaluationEngine",
    "GradingResponseError",
    "RubricResponseError",
    "ChatResponseError",
    "AnalyticsResponseError",
]
