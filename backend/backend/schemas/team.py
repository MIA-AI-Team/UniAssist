import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    name: str = Field(min_length=2, max_length=150)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Choose a team name")
        return value.strip()


class TeamAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    expected_version: int = Field(gt=0)
    action: Literal["invite", "remove", "cancel_invitation", "leave", "archive", "request_approval", "approve", "reject"]
    student_number: str | None = Field(default=None, min_length=1, max_length=50)
    student_id: int | None = Field(default=None, gt=0)
    invitation_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def action_fields(self):
        expected = {"invite": "student_number", "remove": "student_id", "cancel_invitation": "invitation_id"}.get(self.action)
        for field in ("student_number", "student_id", "invitation_id"):
            if (getattr(self, field) is not None) != (expected == field):
                raise ValueError("Invalid action fields")
        return self


class InvitationReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    expected_version: int = Field(gt=0)
    decision: Literal["accept", "decline"]


class RosterMember(BaseModel):
    student_id: int
    name: str
    student_number: str
    accepted_at: dt.datetime | None


class TeamSnapshot(BaseModel):
    team_id: int
    name: str
    version: int
    members: list[RosterMember]


class InvitationInfo(BaseModel):
    id: int
    team_id: int
    task_id: int
    team_name: str
    student_id: int
    name: str
    status: str
    created_at: dt.datetime


class TeamInfo(BaseModel):
    id: int
    task_id: int
    name: str
    created_by: int | None
    status: str
    version: int
    locked_at: dt.datetime | None
    members: list[RosterMember]
    invitations: list[InvitationInfo]
    actions: list[str]
    unavailable_reason: str | None


class TeamList(BaseModel):
    items: list[TeamInfo]
    next_cursor: int | None


class InvitationList(BaseModel):
    items: list[InvitationInfo]
    next_cursor: int | None


class TeamEventInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    version: int
    roster: TeamSnapshot
    created_at: dt.datetime


class TeamEventList(BaseModel):
    items: list[TeamEventInfo]
    next_cursor: int | None


class TeamMutationResult(BaseModel):
    team_id: int
    version: int
