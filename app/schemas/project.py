from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from .place import PlaceCreate, PlaceOut

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["Chicago Art Tour"])
    description: str | None = Field(None, examples=["Exploring art museums in Chicago"])
    start_date: date | None = Field(None, examples=["2024-06-01"])
    places: list[PlaceCreate] | None = Field(None, examples=[[{"external_id": "27992", "notes": "Must see"}, {"external_id": "28560", "notes": "Check opening hours"}]])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Chicago Art Tour",
                "description": "Exploring art museums in Chicago",
                "start_date": "2024-06-01",
                "places": [
                    {"external_id": "27992", "notes": "Must see - famous painting"},
                    {"external_id": "28560", "notes": "Check opening hours before visit"}
                ]
            }
        }
    )

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200, examples=["Updated Chicago Art Tour"])
    description: str | None = Field(None, examples=["Updated description"])
    start_date: date | None = Field(None, examples=["2024-07-01"])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Chicago Art Tour",
                "description": "Updated description",
                "start_date": "2024-07-01"
            }
        }
    )

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    completed: bool

    model_config = ConfigDict(from_attributes=True)

class ProjectDetailOut(ProjectOut):
    places: list[PlaceOut]
