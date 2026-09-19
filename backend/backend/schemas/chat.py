import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr


class ChatCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    language: Literal["en", "ar"] = "en"
    submission_id: int | None = Field(default=None, gt=0)


class ChatSend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    content: str = Field(min_length=1, max_length=4000)
    retry: bool = False

    @field_validator("content")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value


class ChatInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int | None
    submission_id: int | None
    title: str
    language: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ChatList(BaseModel):
    items: list[ChatInfo]
    next_cursor: int | None


class TutorContextInfo(BaseModel):
    task_id: int
    reference_file_id: int | None = None
    rubric_version: int | None = None
    submission_id: int | None = None
    released_feedback: bool = False
    truncated: bool = False
    lab_mode: str | None = None


class TutorMetadata(BaseModel):
    provider: str | None = None
    model_used: str | None = None
    prompt_version: str | None = None
    ai_engine_version: str | None = None
    latency_ms: float
    output_sanitized: bool = False


class ChatTurnInfo(BaseModel):
    id: int
    request_id: str
    content: str
    reply: str | None
    status: Literal["pending", "completed", "failed"]
    error_code: str | None
    retryable: bool
    is_mock: bool | None
    context_info: TutorContextInfo | None
    ai_metadata: TutorMetadata | None = None
    created_at: dt.datetime


class ChatTurnList(BaseModel):
    items: list[ChatTurnInfo]
    next_cursor: int | None


class ShareCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    recipient_email: EmailStr
    through_turn_id: int = Field(gt=0)
    preview_turn_ids: list[int] = Field(min_length=1, max_length=200)


class SharedTurn(BaseModel):
    id: int
    content: str
    reply: str
    is_mock: bool | None
    created_at: dt.datetime


class ShareInfo(BaseModel):
    id: int
    session_id: int
    task_id: int | None
    title: str
    student_name: str
    recipient_name: str
    through_turn_id: int
    created_at: dt.datetime
    revoked_at: dt.datetime | None


class ShareDetail(ShareInfo):
    snapshot: list[SharedTurn]


class ShareList(BaseModel):
    items: list[ShareInfo]
    next_cursor: int | None


class TutorSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    lab_mode: Literal["experiment", "coding"] = "experiment"


class LegacyMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_type: Literal["user", "assistant"]
    content: str
    created_at: dt.datetime


class LegacyMessages(BaseModel):
    items: list[LegacyMessage]
    next_cursor: int | None
