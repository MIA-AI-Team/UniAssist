from __future__ import annotations

import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.schemas.rubric import RubricCriterionInput
from backend.schemas.team import TeamSnapshot
from backend.schemas.repository import SnapshotInfo


# ---------------------------------------------------------------------------
# Input Request Schemas
# ---------------------------------------------------------------------------

class CreateSubmissionRequest(BaseModel):
    task_id: int
    submission_text: str = ""
    team_id: Optional[int] = None
    file_id: Optional[int] = None
    repository_snapshot_id: int | None = Field(None,gt=0)

class CreateSubmissionForm(CreateSubmissionRequest):
    """Deprecated import alias. Submission transport is JSON, not multipart."""
class ConfirmGradeRequest(BaseModel):
    final_grade: float = Field(ge=0, allow_inf_nan=False)


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
    total_possible_grade: Optional[float] = None

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


class ArtifactResponse(BaseModel):
    file_id: int
    file_name: str
    file_type: str

class CriterionEvaluationResponse(BaseModel):
    criterion_name: str
    score_given: float
    max_points: float
    reasoning: str

class CodeFindingResponse(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    severity: str
    finding: str

class SubmissionDetailResponse(BaseModel):
    repository_snapshot: SnapshotInfo | None = None
    team_snapshot: TeamSnapshot | None = None
    grading_guidance_id: int | None = None
    grading_guidance_version: int | None = None
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
    rubric_id: int
    rubric_version: int
    total_possible_grade: float
    rubric_criteria: list[RubricCriterionInput] = Field(default_factory=list)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    criterion_evaluations: Optional[list[CriterionEvaluationResponse]] = None
    code_reviews: Optional[list[CodeFindingResponse]] = None
    ai_warnings: Optional[list[str]] = None
    is_mock: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionQueueItem(SubmissionListItemResponse):
    student_id: int
    student_name: str
    student_number: str
