from pydantic import BaseModel, Field
import datetime as dt
class RubricUploadResponse(BaseModel):
    rubric_id: int
    version: int
    status: str


class RubricCriterionInput(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    max_points: float = Field(gt=0, allow_inf_nan=False)
    sort_order: int | None = None


class CreateRubricRequest(BaseModel):
    criteria: list[RubricCriterionInput] = Field(min_length=1)

class RefineRequest(BaseModel):
    staff_feedback: str = Field(min_length=1)


class StatusRequest(BaseModel):
    status: str

class RubricCreatedResponse(RubricUploadResponse):
    criteria: list[RubricCriterionInput]

class RubricListItem(BaseModel):
    id: int
    version: int
    source: str
    status: str
    reviewed_at: dt.datetime | None = None
    criteria: list[RubricCriterionInput]


class ApprovedRubricResponse(BaseModel):
    """Student-facing grading expectations, never assessment output or staff drafts."""
    id: int
    version: int
    total: float
    criteria: list[RubricCriterionInput]
