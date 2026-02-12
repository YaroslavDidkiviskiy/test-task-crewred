from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class PlaceCreate(BaseModel):
    external_id: str = Field(..., min_length=1, examples=["27992"], description="Numeric ID from ArtIC API (e.g., 27992, 28560)")
    notes: str | None = Field(None, examples=["Must see - famous painting"])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "external_id": "27992",
                "notes": "Must see - famous painting"
            }
        }
    )

class PlaceUpdate(BaseModel):
    notes: str | None = Field(None, examples=["Visited on 2024-06-15. Amazing!"])
    visited: bool | None = Field(None, examples=[True])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notes": "Visited on 2024-06-15. Amazing!",
                "visited": True
            }
        }
    )

class PlaceOut(BaseModel):
    id: int
    external_id: str
    title: str | None
    notes: str | None
    visited: bool
    visited_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
