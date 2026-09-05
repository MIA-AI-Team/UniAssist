"""Chat session contracts aligned with backend CHAT_SESSIONS / CHAT_MESSAGES."""

from __future__ import annotations

from typing import List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from ai_tutor.models.chat import ChatMessage


class ChatSessionScope(BaseModel):
    """
    Scopes a chat turn to a persisted backend session.

    Backend owns CHAT_SESSIONS rows; pass these ids so context stays on the
    correct task/submission and can be audited in ai_metadata.
    """

    session_id: Optional[int] = Field(default=None, description="CHAT_SESSIONS.id")
    task_id: Optional[int] = Field(default=None, description="CHAT_SESSIONS.task_id → load spec/lab context")
    submission_id: Optional[int] = Field(
        default=None,
        description="CHAT_SESSIONS.submission_id — optional link to student work",
    )


class PersistedChatMessage(BaseModel):
    """One CHAT_MESSAGES row shape (backend → AI history conversion)."""

    sender_type: str = Field(description="user|assistant|system (CHAT_MESSAGES.sender_type)")
    content: str


_SENDER_TO_ROLE = {
    "user": "user",
    "assistant": "assistant",
    "system": "system",
}


def sender_type_to_role(sender_type: str) -> str:
    key = (sender_type or "").strip().lower()
    if key not in _SENDER_TO_ROLE:
        raise ValueError(f"Unsupported CHAT_MESSAGES.sender_type: {sender_type!r}")
    return _SENDER_TO_ROLE[key]


def role_to_sender_type(role: str) -> str:
    key = (role or "").strip().lower()
    if key in ("user", "assistant", "system"):
        return key
    raise ValueError(f"Unsupported chat role: {role!r}")


def chat_history_from_persisted(
    messages: Sequence[Union[PersistedChatMessage, dict]],
    *,
    max_messages: Optional[int] = None,
    include_system: bool = False,
) -> List[ChatMessage]:
    """
    Convert stored CHAT_MESSAGES into AI chat_history (continue-later support).

    Backend loads messages for a session ordered by created_at ASC, then calls this
    (or passes ChatMessage list directly). When max_messages is set, keeps the
    most recent N messages.
    """
    history: List[ChatMessage] = []
    for raw in messages:
        if isinstance(raw, PersistedChatMessage):
            msg = raw
        else:
            msg = PersistedChatMessage(**raw)
        sender = (msg.sender_type or "").strip().lower()
        if sender == "system" and not include_system:
            continue
        content = (msg.content or "").strip()
        if not content:
            continue
        history.append(ChatMessage(role=sender_type_to_role(sender), content=content))

    if max_messages is not None and max_messages > 0 and len(history) > max_messages:
        return history[-max_messages:]
    return history


def trim_chat_history(history: Sequence[ChatMessage], max_messages: int) -> List[ChatMessage]:
    """Keep the most recent messages for the model context window."""
    items = list(history)
    if max_messages <= 0 or len(items) <= max_messages:
        return items
    return items[-max_messages:]


def scope_as_metadata(scope: Optional[ChatSessionScope]) -> dict:
    if scope is None:
        return {}
    data = scope.model_dump(exclude_none=True)
    return data
