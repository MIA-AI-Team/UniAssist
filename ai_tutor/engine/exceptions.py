class GradingResponseError(Exception):
    """Raised when the LLM grading response cannot be parsed or validated."""


class RubricResponseError(Exception):
    """Raised when the LLM rubric response cannot be parsed or validated."""


class ChatResponseError(Exception):
    """Raised when the LLM chat response fails."""
