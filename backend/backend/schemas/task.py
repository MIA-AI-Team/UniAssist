from __future__ import annotations

import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime
from typing import Literal
from backend.schemas.submission import SubmissionListItemResponse
from backend.schemas.rubric import ApprovedRubricResponse


# ---------------------------------------------------------------------------
# Input Request Schemas
# ---------------------------------------------------------------------------

class CreateTaskRequest(BaseModel):
    type: Literal["lab", "assignment", "project"]
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    due_date: AwareDatetime
    target_cohort_year: int = Field(ge=1)
    target_major: Optional[str] = None
    reference_file_id: Optional[int] = None
    

    # Lab fields
    scheduled_date: Optional[AwareDatetime] = None

    # Assignment fields
    allowed_file_types: list[str] = Field(default_factory=lambda: ["pdf", "zip"], min_length=1)
    allow_late: bool = False

    # Project fields
    default_repo_provider: Optional[str] = "github"
    require_team: bool = True


# ---------------------------------------------------------------------------
# Output Response Schemas
# ---------------------------------------------------------------------------

class TaskLabDetailsResponse(BaseModel):
    scheduled_date: Optional[dt.datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TaskAssignmentDetailsResponse(BaseModel):
    allowed_file_types: Optional[list[str]] = None
    allow_late: bool = False

    model_config = ConfigDict(from_attributes=True)


class TaskProjectDetailsResponse(BaseModel):
    default_repo_provider: Optional[str] = None
    require_team: bool = True

    model_config = ConfigDict(from_attributes=True)


class SubmissionEligibility(BaseModel):
    team_id: int | None = None
    allowed: bool
    reason_code: Optional[str] = None
    rubric_ready: bool
    rubric_total: Optional[float] = None

class TaskListItemResponse(BaseModel):
    id: int
    type: str
    title: str
    description: str
    due_date: dt.datetime
    target_cohort_year: int
    target_major: Optional[str] = None
    reference_file_id: Optional[int] = None
    latest_submission: Optional[SubmissionListItemResponse] = None
    review_counts: Optional[dict[str, int]] = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskListItemResponse):
    created_by: int
    created_at: dt.datetime
    submission_eligibility: SubmissionEligibility
    accepted_rubric: Optional[ApprovedRubricResponse] = None

    lab_details: Optional[TaskLabDetailsResponse] = None
    assignment_details: Optional[TaskAssignmentDetailsResponse] = None
    project_details: Optional[TaskProjectDetailsResponse] = None


class TaskCreatedResponse(BaseModel):
    id: int
    type: str
    title: str
    due_date: dt.datetime
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)
