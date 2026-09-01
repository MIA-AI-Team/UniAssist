from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.chat import ChatMessage
from ai_tutor.models.rubric import RubricCriteriaItem


class RubricSuggestRequest(BaseModel):
    task_title: str
    task_type: str = "lab"
    task_description: str = ""
    reference_text: str = ""
    request_metadata: Optional[Dict[str, Any]] = None


class RubricRefineRequest(BaseModel):
    task_title: str
    task_type: str = "lab"
    task_description: str = ""
    reference_text: str = ""
    previous_criteria: List[RubricCriteriaItem]
    staff_feedback: str
    request_metadata: Optional[Dict[str, Any]] = None


class GradeSubmissionRequest(BaseModel):
    task_title: str
    task_type: str = "lab"
    reference_text: str
    rubric_criteria: List[RubricCriteriaItem]
    submission_text: str = ""
    code_files: Dict[str, str] = Field(default_factory=dict)
    grading_key: Optional[str] = None
    request_metadata: Optional[Dict[str, Any]] = None


class SocraticChatRequest(BaseModel):
    reference_text: str = ""
    chat_history: List[ChatMessage] = Field(default_factory=list)
    student_message: str
    task_title: Optional[str] = None
    request_metadata: Optional[Dict[str, Any]] = None


class LabAssistantChatRequest(BaseModel):
    lab_title: str
    lab_type: str = "experiment"
    steps_and_theory: str = ""
    model_answers: str = ""
    chat_history: List[ChatMessage] = Field(default_factory=list)
    student_message: str
    request_metadata: Optional[Dict[str, Any]] = None
