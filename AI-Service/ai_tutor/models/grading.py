from typing import List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.metadata import AIMetadata


class CriterionEvaluation(BaseModel):
    criterion_name: str
    score_given: float = Field(ge=0)
    max_points: float = Field(gt=0)
    reasoning: str


class CodeReviewFinding(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    severity: str
    finding: str


class SubmissionGradingResponse(BaseModel):
    ai_suggested_grade: float = Field(ge=0)
    total_possible_grade: float = Field(gt=0)
    percentage: float = Field(ge=0, le=100)
    summary_feedback: str
    criterion_evaluations: List[CriterionEvaluation]
    code_reviews: List[CodeReviewFinding] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ai_metadata: Optional[AIMetadata] = None
    professor_notes: Optional[str] = None
