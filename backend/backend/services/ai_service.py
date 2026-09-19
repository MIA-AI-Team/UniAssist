from __future__ import annotations

from typing import Any, Callable
import asyncio
import time
from sqlalchemy import update
from backend.database import AsyncSessionLocal
from backend.models.operations import AIOperation

from fastapi.concurrency import run_in_threadpool

from ai_tutor import RubricResponseError, GradingResponseError, ChatResponseError, AnalyticsResponseError
from backend.services.exceptions import (
    AIRequestError,
    AIServiceError,
    AIRubricError,
)


async def call_ai(
    function: Callable,
    payload: Any,
    *,
    context_truncated: bool = False,
):
    # No identity, input/output, exception message or arbitrary metadata is persisted.
    # Separate transactions retain failed calls even when the academic transaction rolls back.
    allowed = {"suggest_rubric", "refine_rubric", "grade_submission", "socratic_chat",
               "lab_assistant_chat", "analyze_cohort_patterns"}
    operation = getattr(function, "__name__", "unknown")
    operation = operation if operation in allowed else "unknown"
    actual_mock = getattr(getattr(getattr(function, "__self__", None), "engine", None), "mock_mode", None)
    async with AsyncSessionLocal() as metrics_db:
        row = AIOperation(operation=operation, provider="mock" if actual_mock else "unknown",
            outcome="started", latency_ms=0, is_mock=actual_mock, truncated=None)
        metrics_db.add(row)
        await metrics_db.commit()
        record_id = row.id
    started = time.monotonic()
    result = None
    outcome = "error"
    try:
        result = await run_in_threadpool(
            function,
            payload,
        )
        outcome = "success"
        return result

    except ValueError as e:
        raise AIRequestError(str(e)) from e

    except (RubricResponseError, GradingResponseError) as e:
        raise AIRubricError(str(e)) from e

    except (ChatResponseError, AnalyticsResponseError) as e:
        raise AIServiceError(str(e)) from e

    except RuntimeError as e:
        raise AIServiceError(str(e)) from e

    finally:
        metadata = getattr(result, "ai_metadata", None)
        provider = "mock" if actual_mock else getattr(metadata, "provider", None)
        provider = provider if provider in {"mock", "groq", "gemini"} else "unknown"
        values = dict(outcome=outcome, latency_ms=round((time.monotonic() - started) * 1000, 2),
            provider=provider, truncated=bool(context_truncated or metadata.prompt_truncated) if metadata else None)
        async def persist():
            async with AsyncSessionLocal() as metrics_db:
                await metrics_db.execute(update(AIOperation).where(AIOperation.id == record_id).values(**values))
                await metrics_db.commit()
        await asyncio.shield(persist())

