from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.deps.db import get_db
from app.schemas import PlaceCreate, PlaceUpdate, PlaceOut
from app.crud import project as project_crud
from app.crud import place as place_crud
from app.services.project_service import add_place, update_place

router = APIRouter()

@router.post("/{project_id}/places", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
async def add_project_place(project_id: int, payload: PlaceCreate, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return await add_place(db, project, payload.external_id, payload.notes)

@router.get("/{project_id}/places", response_model=list[PlaceOut])
def list_project_places(project_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return place_crud.list_for_project(db, project_id, limit=min(limit, 100), offset=offset)

@router.get("/{project_id}/places/{place_id}", response_model=PlaceOut)
def get_project_place(project_id: int, place_id: int, db: Session = Depends(get_db)):
    place = place_crud.get(db, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(404, "Place not found")
    return place

@router.patch("/{project_id}/places/{place_id}", response_model=PlaceOut)
def patch_project_place(project_id: int, place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    place = place_crud.get(db, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(404, "Place not found")

    return update_place(db, project, place, payload.notes, payload.visited)
