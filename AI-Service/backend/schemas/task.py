from __future__ import annotations

import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Input Request Schemas
# ---------------------------------------------------------------------------

class CreateTaskRequest(BaseModel):
    type: str                           # lab | assignment | project
    title: str
    description: str
    due_date: dt.datetime
    target_cohort_year: int
    target_major: Optional[str] = None
    reference_file_id: Optional[int] = None
    

    # Lab fields
    scheduled_date: Optional[dt.datetime] = None

    # Assignment fields
    allowed_file_types: Optional[list[str]] = ["pdf", "zip"]
    allow_late: Optional[bool] = False

    # Project fields
    default_repo_provider: Optional[str] = "github"
    require_team: Optional[bool] = True


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


class TaskListItemResponse(BaseModel):
    id: int
    type: str
    title: str
    description: str
    due_date: dt.datetime
    target_cohort_year: int
    target_major: Optional[str] = None
    reference_file_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskListItemResponse):
    created_by: int
    created_at: dt.datetime

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