import uuid
from typing import Optional, List
from pydantic import BaseModel


class LabBase(BaseModel):
    title: str
    slug: str
    description: str
    difficulty: str
    duration: str
    category: str
    icon: str
    estimated_time: str
    status: str
    coming_soon: bool


class LabResponse(LabBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class LabListResponse(BaseModel):
    labs: List[LabResponse]
    total: int
