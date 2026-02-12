from pydantic import BaseModel, Field
from datetime import date
from .place import PlaceCreate, PlaceOut

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None
    places: list[PlaceCreate] | None = None

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    start_date: date | None = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    completed: bool

    class Config:
        from_attributes = True

class ProjectDetailOut(ProjectOut):
    places: list[PlaceOut]
