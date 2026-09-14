from __future__ import annotations

import datetime as dt
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class FileUploadParams(BaseModel):
    purpose: Literal["reference", "submission", "other"] = Field(
        ..., description="Purpose of the uploaded file"
    )
    task_id: Optional[int] = None
    submission_id: Optional[int] = None



class FileUploadResponse(BaseModel):
    file_id: int
    file_name: Optional[str] = None
    file_type: str
    purpose: str
    storage_path: str
    uploaded_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class FileInfoResponse(BaseModel):
    file_id: int
    file_type: str
    purpose: str
    task_id: Optional[int] = None
    submission_id: Optional[int] = None
    storage_path: str
    uploaded_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)