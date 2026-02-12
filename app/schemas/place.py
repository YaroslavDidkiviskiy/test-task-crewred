from pydantic import BaseModel, Field
from datetime import datetime

class PlaceCreate(BaseModel):
    external_id: str = Field(..., min_length=1)
    notes: str | None = None

class PlaceUpdate(BaseModel):
    notes: str | None = None
    visited: bool | None = None

class PlaceOut(BaseModel):
    id: int
    external_id: str
    title: str | None
    notes: str | None
    visited: bool
    visited_at: datetime | None

    class Config:
        from_attributes = True
