from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.deps.db import get_db
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut
from app.models import Project
from app.crud import project as project_crud
from app.services.project_service import can_delete, create_project_with_places

router = APIRouter()

@router.post("", response_model=ProjectDetailOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description, start_date=payload.start_date)
    
    # Project must have at least 1 place (requirement: minimum 1, maximum 10)
    if not payload.places:
        raise HTTPException(422, "Project must have at least 1 place")
    
    return await create_project_with_places(db, project, payload.places)

@router.get("", response_model=list[ProjectOut])
def list_projects(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    return project_crud.list_all(db, limit=min(limit, 100), offset=offset)

@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectDetailOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.start_date is not None:
        project.start_date = payload.start_date

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not can_delete(project):
        raise HTTPException(409, "Cannot delete project with visited places")
    project_crud.delete(db, project)
    return None
