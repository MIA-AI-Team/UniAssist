import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from ai_tutor.models.analytics import CommonIssue, Misconception
from backend.schemas.chat import TutorMetadata


class GuidanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    content: str = Field(max_length=12000)


class GuidanceInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int
    version: int
    content: str
    created_by: int
    created_at: dt.datetime


class GuidanceList(BaseModel):
    items: list[GuidanceInfo]
    next_cursor: int | None


class CriterionStatistic(BaseModel):
    criterion_id: int
    name: str
    label: str
    max_points: float
    sample_count: int
    average_score: float | None
    low_score_count: int | None


class RubricGroup(BaseModel):
    rubric_id: int
    rubric_version: int
    student_count: int
    eligible: bool
    average_percentage: float | None
    minimum_percentage: float | None
    maximum_percentage: float | None
    below_half_count: int | None
    criteria: list[CriterionStatistic]
    severity_counts: dict[str, int] | None
    mock_assessment_count: int
    unknown_provenance_count: int


class TaskAnalytics(BaseModel):
    task_id: int
    minimum_group_size: int
    released_count: int
    excluded_count: int
    input_fingerprint: str
    groups: list[RubricGroup]


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    rubric_id: int = Field(gt=0)
    language: Literal["en", "ar"] = "en"


class TeachingSuggestions(BaseModel):
    summary: str = Field(min_length=1, max_length=8000)
    common_issues: list[CommonIssue] = Field(default_factory=list, max_length=30)
    misconceptions: list[Misconception] = Field(default_factory=list, max_length=30)
    teaching_focus: list[str] = Field(default_factory=list, max_length=30)
    warnings: list[str] = Field(default_factory=list, max_length=30)


class TeachingReportInfo(BaseModel):
    id: int
    task_id: int
    rubric_id: int
    rubric_version: int
    language: str
    input_fingerprint: str
    input_snapshot: RubricGroup
    result: TeachingSuggestions
    is_mock: bool
    ai_metadata: TutorMetadata | None
    created_at: dt.datetime
    stale: bool


class TeachingReportList(BaseModel):
    items: list[TeachingReportInfo]
    next_cursor: int | None
