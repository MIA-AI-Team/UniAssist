from typing import Dict, Optional

from pydantic import BaseModel, Field

from ai_tutor.models.grading import SubmissionGradingResponse


class LabItem(BaseModel):
    id: str
    title: str
    lab_type: str = "experiment"
    description: str = ""
    steps_and_theory: str = ""
    model_answers: str = ""
    rubric_json: Optional[str] = "[]"


class LabSubmission(BaseModel):
    id: str
    lab_id: str
    student_name: str
    student_id: str
    submission_text: str
    code_files: Dict[str, str] = Field(default_factory=dict)
    submitted_at: str
    status: str = "submitted"
    grade_result: Optional[SubmissionGradingResponse] = None
    professor_notes: Optional[str] = None
    task_title: Optional[str] = None
