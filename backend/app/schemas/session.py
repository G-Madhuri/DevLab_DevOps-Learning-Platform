import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class LabSessionBase(BaseModel):
    lab_name: str


class LabSessionCreate(LabSessionBase):
    pass


class LabSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    lab_name: str
    container_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LabSessionListResponse(BaseModel):
    sessions: List[LabSessionResponse]
    total: int


class TaskValidationRequest(BaseModel):
    task_id: int
    course_slug: Optional[str] = None


class TaskValidationResponse(BaseModel):
    success: bool
    message: str
