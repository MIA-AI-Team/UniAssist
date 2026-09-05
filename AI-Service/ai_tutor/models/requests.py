from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.analytics import (
    CohortCodeReviewSnapshot,
    CohortCriterionSnapshot,
    CohortGradeSnapshot,
)
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


class CohortAnalyticsRequest(BaseModel):
    """
    Cohort-level pattern analysis for staff (TA/professor).

    Backend must anonymize inputs — no student names, emails, or IDs required.
    Auth and DB aggregation stay in the backend service.
    """

    task_title: str
    task_type: str = "lab"
    task_description: str = ""
    rubric_criteria_names: List[str] = Field(default_factory=list)
    grades: List[CohortGradeSnapshot] = Field(default_factory=list)
    code_reviews: List[CohortCodeReviewSnapshot] = Field(default_factory=list)
    criterion_stats: List[CohortCriterionSnapshot] = Field(default_factory=list)
    request_metadata: Optional[Dict[str, Any]] = None
