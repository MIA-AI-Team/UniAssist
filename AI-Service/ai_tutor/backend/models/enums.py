
from __future__ import annotations
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    professor = "professor"
    teaching_assistant = "teaching_assistant"
    student = "student"
 
 
class TaskType(str, enum.Enum):
    lab = "lab"
    assignment = "assignment"
    project = "project"
 
 
class RubricSource(str, enum.Enum):
    ai_suggested = "ai_suggested"
    staff_created = "staff_created"
 
 
class RubricStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    replaced = "replaced"
 
 
class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    ai_graded = "ai_graded"
    staff_confirmed = "staff_confirmed"
 
 
class ReviewType(str, enum.Enum):
    static_analysis = "static_analysis"
    ai_code_review = "ai_code_review"
 
 
class Severity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"
 
 
class SenderType(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
 