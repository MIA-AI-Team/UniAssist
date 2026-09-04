from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AIMetadata(BaseModel):
    """Observability metadata attached to every AI response for backend persistence."""

    ai_engine_version: str = Field(description="AI engine semantic version")
    prompt_version: str = Field(description="Prompt template bundle version")
    operation: str = Field(default="", description="AI operation name")
    provider: Optional[str] = Field(default=None, description="LLM provider used")
    model_used: Optional[str] = Field(default=None, description="Model identifier used")
    latency_ms: Optional[float] = Field(default=None, description="End-to-end AI call latency")
    parse_success: bool = Field(default=True, description="Whether structured output parsed successfully")
    prompt_truncated: bool = Field(default=False, description="Whether input context was truncated")
    scores_adjusted: bool = Field(default=False, description="Whether post-processing adjusted AI scores")
    output_sanitized: bool = Field(default=False, description="Whether output was sanitized (e.g. anti-leak)")
    warnings_count: int = Field(default=0, description="Number of non-fatal warnings")
    completed_at: Optional[str] = Field(default=None, description="ISO-8601 UTC completion timestamp")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Opaque metadata from caller")
