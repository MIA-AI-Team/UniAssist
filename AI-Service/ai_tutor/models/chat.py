from typing import List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.metadata import AIMetadata


class ChatMessage(BaseModel):
    role: str
    content: str


class StudentChatRequest(BaseModel):
    task_title: Optional[str] = "Assignment Guidance"
    reference_text: Optional[str] = ""
    chat_history: List[ChatMessage] = Field(default_factory=list)
    student_message: str


class StudentChatResponse(BaseModel):
    reply: str
    session_id: Optional[int] = Field(
        default=None,
        description="Echo of CHAT_SESSIONS.id so backend can append CHAT_MESSAGES",
    )
    ai_metadata: Optional[AIMetadata] = None


class LabChatRequest(BaseModel):
    lab_id: str
    student_message: str
    chat_history: List[ChatMessage] = Field(default_factory=list)


class LabChatResponse(BaseModel):
    reply: str
    detected_mode: str = "experiment_guide"
    session_id: Optional[int] = Field(
        default=None,
        description="Echo of CHAT_SESSIONS.id so backend can append CHAT_MESSAGES",
    )
    ai_metadata: Optional[AIMetadata] = None
