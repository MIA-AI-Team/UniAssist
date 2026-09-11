from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tasks import TaskLabDetails
from backend.models.chat import ChatMessage, ChatSession
from backend.repository.rubric_repository import get_accepted_rubric
from backend.repository.embedding_repository import get_reference_text
from backend.repository.task_repository import _get_task
from ai_tutor.models import RubricCriteriaItem
from ai_tutor.models.chat_session import PersistedChatMessage


async def get_task_context(
    task_id: int,
    db: AsyncSession,
) -> dict:
    task = await _get_task(task_id, db)

    rubric = await get_accepted_rubric(task_id, db)

    rubric_criteria = [
        RubricCriteriaItem(
            name=criterion.name,
            description=criterion.description,
            max_points=criterion.max_points,
            sort_order=criterion.sort_order,
        )
        for criterion in sorted(
            rubric.criteria,
            key=lambda criterion: criterion.sort_order,
        )
    ]

    reference_text = (
        await get_reference_text(task_id, db)
        or task.description
    )

    lab_steps = ""
    model_answers = ""

    if task.type.value == "lab":
        result = await db.execute(
            select(TaskLabDetails)
            .where(TaskLabDetails.task_id == task_id)
        )

        lab_details = result.scalar_one_or_none()

        if lab_details:
            lab_steps = task.description

    return {
        "task_title": task.title,
        "task_type": task.type.value,
        "task_description": task.description,
        "reference_text": reference_text,
        "rubric_criteria": rubric_criteria,
        "lab_steps": lab_steps,
        "model_answers": model_answers,
    }


async def get_chat_history(
    session_id: int,
    db: AsyncSession,
) -> list[PersistedChatMessage]:
    """
    Load all CHAT_MESSAGES for a session ordered by created_at ASC.

    Returns a list of PersistedChatMessage ready to pass directly to:
        - ai.build_chat_history(rows)
        - SocraticChatRequest(persisted_messages=rows, ...)
    """

    # Verify session exists
    session_result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )

    session: ChatSession | None = session_result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session {session_id} not found.",
        )

    # Load messages ordered ASC
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )

    messages: list[ChatMessage] = list(
        messages_result.scalars().all()
    )

    return [
        PersistedChatMessage(
            sender_type=msg.sender_type.value,
            content=msg.content,
        )
        for msg in messages
    ]


async def get_session(
    session_id: int,
    db: AsyncSession,
) -> ChatSession:
    """
    Load a CHAT_SESSIONS row by id.
    """

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )

    session: ChatSession | None = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session {session_id} not found.",
        )

    return session
