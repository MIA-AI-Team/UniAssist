import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RepositoryProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    repo_url: str = Field(min_length=3,max_length=250)


class RepositoryAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    expected_version: int = Field(gt=0)
    action: Literal["approve","reject","sync","attribute"]
    commit_id: int | None = Field(None,gt=0)
    student_id: int | None = Field(None,gt=0)

    @model_validator(mode="after")
    def fields_for_action(self):
        if self.action=="attribute" and self.commit_id is None:
            raise ValueError("Choose a commit")
        if self.action!="attribute" and (self.commit_id is not None or self.student_id is not None):
            raise ValueError("Unexpected attribution fields")
        return self


class SnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")


class ManifestFile(BaseModel):
    path: str
    size: int
    sha256: str
    included: bool


class SnapshotProvenance(BaseModel):
    task_id: int
    team_id: int
    repository_id: int
    repo_url: str
    github_id: int
    commit_sha: str
    archive_sha256: str
    compressed_bytes: int
    captured_at: dt.datetime
    team_version: int
    repository_version: int
    is_fixture: bool
    files: list[ManifestFile]
    omitted_files: int
    attribution: list[dict]


class SnapshotInfo(BaseModel):
    id: int
    repository_id: int
    commit_sha: str
    created_at: dt.datetime
    provenance: SnapshotProvenance
    model_config = ConfigDict(from_attributes=True)


class RepositoryInfo(BaseModel):
    id: int
    task_id: int
    team_id: int
    repo_url: str | None
    full_name: str | None
    status: str
    version: int
    approved_team_version: int | None
    last_synced_at: dt.datetime | None
    sync_error: str | None
    partial_history: bool
    is_fixture: bool
    actions: list[str]
    unavailable_reason: str | None


class RepositoryList(BaseModel):
    items: list[RepositoryInfo]
    next_cursor: int | None


class CommitInfo(BaseModel):
    id: int
    commit_hash: str
    author_name: str
    author_github_username: str
    message: str
    committed_at: dt.datetime
    student_id: int | None
    attributed_by: int | None
    attributed_at: dt.datetime | None
    model_config = ConfigDict(from_attributes=True)


class CommitList(BaseModel):
    items: list[CommitInfo]
    next_cursor: int | None


class RepositoryEventInfo(BaseModel):
    id: int
    actor_id: int
    action: str
    version: int
    details: dict
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)


class RepositoryEventList(BaseModel):
    items: list[RepositoryEventInfo]
    next_cursor: int | None


class RepositoryReceipt(BaseModel):
    repository_id: int
    version: int
