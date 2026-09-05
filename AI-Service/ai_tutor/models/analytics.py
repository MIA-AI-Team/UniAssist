from typing import List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.metadata import AIMetadata


class CohortGradeSnapshot(BaseModel):
    """Anonymized per-submission grade row prepared by the backend."""

    grade: float = Field(ge=0, description="ai_suggested_grade or final_grade")
    max_grade: float = Field(gt=0, description="Total possible points for the task")
    feedback: str = Field(default="", description="Anonymized feedback text (no student names)")


class CohortCodeReviewSnapshot(BaseModel):
    """Anonymized code-review finding prepared by the backend."""

    severity: str = Field(description="info|warning|critical")
    finding: str
    file_path: Optional[str] = None
    count: int = Field(default=1, ge=1, description="How often this pattern appeared")


class CohortCriterionSnapshot(BaseModel):
    """Optional aggregated criterion performance (if backend stores criterion scores)."""

    criterion_name: str
    average_score: float = Field(ge=0)
    max_points: float = Field(gt=0)
    low_score_count: int = Field(default=0, ge=0, description="Students below ~60% on this criterion")


class CommonIssue(BaseModel):
    title: str
    description: str
    severity: str = Field(default="warning", description="info|warning|critical")
    affected_estimate: str = Field(
        default="",
        description="Human-readable estimate, e.g. 'many students' or '~40%'",
    )
    evidence: str = Field(default="", description="What in the cohort data supports this")


class Misconception(BaseModel):
    concept: str
    description: str
    suggested_remediation: str = ""


class CohortAnalyticsResponse(BaseModel):
    task_title: str
    student_count: int = Field(ge=0)
    summary: str
    common_issues: List[CommonIssue] = Field(default_factory=list)
    misconceptions: List[Misconception] = Field(default_factory=list)
    teaching_focus: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ai_metadata: Optional[AIMetadata] = None
