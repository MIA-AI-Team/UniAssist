from typing import List, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.metadata import AIMetadata


class RubricCriteriaItem(BaseModel):
    name: str = Field(description="Name of the evaluation criterion")
    description: str = Field(description="Detailed explanation of what is required")
    max_points: float = Field(gt=0, description="Maximum points for this criterion")
    sort_order: int = Field(default=1, description="Order position in the rubric")


class RubricSuggestionResponse(BaseModel):
    task_title: str
    criteria: List[RubricCriteriaItem]
    total_max_points: float
    rationale: str
    warnings: List[str] = Field(default_factory=list)
    ai_metadata: Optional[AIMetadata] = None
