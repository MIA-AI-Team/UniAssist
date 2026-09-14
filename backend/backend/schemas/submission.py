from __future__ import annotations

import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Input Request Schemas
# ---------------------------------------------------------------------------

class CreateSubmissionRequest(BaseModel):
    task_id: int
    submission_text: str = ""
    team_id: Optional[int] = None
    file_id: Optional[int] = None

class CreateSubmissionForm(BaseModel):
    """Schema for validating form fields sent alongside multipart file uploads."""

    task_id: int 
    submission_text: str | None 
    team_id: str | None 
    file_id: str | None 

    model_config = ConfigDict(from_attributes=True)
class ConfirmGradeRequest(BaseModel):
    final_grade: float


# ---------------------------------------------------------------------------
# Output Response Schemas
# ---------------------------------------------------------------------------

class SubmissionCreatedResponse(BaseModel):
    submission_id: int
    task_id: int
    attempt_number: int
    status: str
    submitted_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionListItemResponse(BaseModel):
    id: int
    attempt_number: int
    is_latest: bool
    status: str
    submitted_at: dt.datetime
    ai_suggested_grade: Optional[float] = None
    final_grade: Optional[float] = None
    feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionGradedResponse(BaseModel):
    submission_id: int
    status: str
    ai_suggested_grade: Optional[float] = None
    feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionConfirmedResponse(BaseModel):
    submission_id: int
    status: str
    final_grade: float
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[dt.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionDetailResponse(BaseModel):
    id: int
    task_id: int
    student_id: int
    team_id: Optional[int] = None
    file_id: Optional[int] = None
    submission_text: Optional[str] = None
    attempt_number: int
    is_latest: bool
    status: str
    ai_suggested_grade: Optional[float] = None
    final_grade: Optional[float] = None
    feedback: Optional[str] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[dt.datetime] = None
    submitted_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)