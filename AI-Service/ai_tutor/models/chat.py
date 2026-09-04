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
    ai_metadata: Optional[AIMetadata] = None


class LabChatRequest(BaseModel):
    lab_id: str
    student_message: str
    chat_history: List[ChatMessage] = Field(default_factory=list)


class LabChatResponse(BaseModel):
    reply: str
    detected_mode: str = "experiment_guide"
    ai_metadata: Optional[AIMetadata] = None
