import datetime as dt
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from backend.schemas.auth import IdentityResponse


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=150)
    github_username: str | None = Field(default=None, max_length=39, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")


class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    is_active: bool | None = None
    role: Literal["teaching_assistant", "professor"] | None = None
    student_number: str | None = Field(default=None, min_length=1, max_length=50)
    cohort_year: int | None = Field(default=None, ge=1, le=9999)
    major: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    github_username: str | None = Field(default=None, max_length=39, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")

    @model_validator(mode="after")
    def nonnull(self):
        for key in self.model_fields_set - {"github_username", "department"}:
            if getattr(self, key) is None:
                raise ValueError("This field cannot be null")
        return self


class AccountInfo(IdentityResponse):
    is_active: bool
    created_at: dt.datetime


class AccountList(BaseModel):
    items: list[AccountInfo]
    next_cursor: int | None


class AuditInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int | None
    action: str
    target_type: str
    target_id: int
    fields: list[str]
    created_at: dt.datetime


class AuditList(BaseModel):
    items: list[AuditInfo]
    next_cursor: int | None


class MetricGroup(BaseModel):
    operation: str
    provider: str
    calls: int
    errors: int
    incomplete: int
    average_latency_ms: float
    mock_calls: int
    unknown_mock_calls: int
    truncated_calls: int
    unknown_truncation_calls: int


class MetricsResponse(BaseModel):
    since: dt.datetime
    groups: list[MetricGroup]
