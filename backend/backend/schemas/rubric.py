from pydantic import BaseModel, Field
class RubricUploadResponse(BaseModel):
    rubric_id: int
    version: int
    status: str


class RubricCriterionInput(BaseModel):
    name: str
    description: str | None = None
    max_points: float = Field(gt=0)
    sort_order: int | None = None


class CreateRubricRequest(BaseModel):
    criteria: list[RubricCriterionInput] = Field(min_length=1)

class RefineRequest(BaseModel):
    staff_feedback: str


class StatusRequest(BaseModel):
    status: str
