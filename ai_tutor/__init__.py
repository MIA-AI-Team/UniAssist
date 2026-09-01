"""
AI Tutor — university AI evaluation engine package.

Backend integration entry point:
    from ai_tutor import AIService
"""

from ai_tutor.config import Config
from ai_tutor.service import AIService
from ai_tutor.engine import (
    AIEvaluationEngine,
    ChatResponseError,
    GradingResponseError,
    RubricResponseError,
)

__version__ = Config.AI_ENGINE_VERSION

__all__ = [
    "AIService",
    "AIEvaluationEngine",
    "Config",
    "GradingResponseError",
    "RubricResponseError",
    "ChatResponseError",
    "__version__",
]
