from __future__ import annotations

from typing import Any, Callable

from fastapi.concurrency import run_in_threadpool

from ai_tutor import RubricResponseError
from backend.services.exceptions import (
    AIRequestError,
    AIServiceError,
    AIRubricError,
)


async def call_ai(
    function: Callable,
    payload: Any,
):
    try:
        return await run_in_threadpool(
            function,
            payload,
        )

    except ValueError as e:
        raise AIRequestError(str(e)) from e

    except RubricResponseError as e:
        raise AIRubricError(str(e)) from e

    except RuntimeError as e:
        raise AIServiceError(str(e)) from e

