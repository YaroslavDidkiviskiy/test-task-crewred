from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Project, ProjectPlace
from app.crud import project as project_crud
from app.crud import place as place_crud
from app.crud.base import create
from .artic_service import get_artwork

MAX_PLACES = 10

def recompute_completed(project: Project) -> None:
    if not project.places:
        project.completed = False
        return
    project.completed = all(p.visited for p in project.places)

def can_delete(project: Project) -> bool:
    return not any(p.visited for p in project.places)

async def create_project_with_places(db: Session, project: Project, places_payload):
    places_payload = places_payload or []
    if not places_payload:
        raise HTTPException(422, "Project must have at least 1 place")
    if not (1 <= len(places_payload) <= MAX_PLACES):
        raise HTTPException(422, "Project must have 1..10 places")

    seen = set()
    for p in places_payload:
        if p.external_id in seen:
            raise HTTPException(409, "Duplicate external_id in request")
        seen.add(p.external_id)

        artwork = await get_artwork(p.external_id)
        if not artwork:
            raise HTTPException(404, f"Place with external_id '{p.external_id}' not found in ArtIC API. Please check the ID is valid.")

        project.places.append(ProjectPlace(
            external_id=p.external_id,
            title=artwork.get("title"),
            notes=p.notes,
        ))

    return create(db, project)

async def add_place(db: Session, project: Project, external_id: str, notes: str | None):
    if place_crud.count_for_project(db, project.id) >= MAX_PLACES:
        raise HTTPException(409, "Project already has 10 places")

    if place_crud.exists_external(db, project.id, external_id):
        raise HTTPException(409, "Place already exists in this project")

    artwork = await get_artwork(external_id)
    if not artwork:
        raise HTTPException(404, f"Place with external_id '{external_id}' not found in ArtIC API. Please check the ID is valid.")

    place = ProjectPlace(
        project_id=project.id,
        external_id=external_id,
        title=artwork.get("title"),
        notes=notes,
    )
    create(db, place)

    db.refresh(project)
    recompute_completed(project)
    db.commit()

    return place

def update_place(db: Session, project: Project, place: ProjectPlace, notes, visited):
    if notes is not None:
        place.notes = notes

    if visited is not None:
        place.visited = visited
        place.visited_at = datetime.now(timezone.utc) if visited else None

    db.refresh(project)
    recompute_completed(project)
    db.commit()
    db.refresh(place)

    return place
