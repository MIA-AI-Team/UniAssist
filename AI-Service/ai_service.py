"""Backward-compatible shim — use `from ai_tutor import AIService` in new code."""

from ai_tutor.service import AIService
from ai_tutor.engine import (
    AnalyticsResponseError,
    ChatResponseError,
    GradingResponseError,
    RubricResponseError,
)

__all__ = [
    "AIService",
    "GradingResponseError",
    "RubricResponseError",
    "ChatResponseError",
    "AnalyticsResponseError",
]
