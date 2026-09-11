
class TaskNotFound(Exception):
    """Raised when the requested task_id does not exist."""

class NoAcceptedRubric(Exception):
    """Raised when a task has no accepted rubric yet."""

class SessionNotFound(Exception):
    """Raised when the requested session_id does not exist."""

class AIServiceError(Exception):
    """Raised when an error occurs in the AI service."""
class AIRubricError(Exception):
    """Raised when an error occurs in the AI service related to rubric generation."""
class AIRequestError(Exception):
    """Raised when an error occurs in the AI service related to request validation."""

