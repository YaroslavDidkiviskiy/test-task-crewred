from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from app.deps.db import get_db
from app.deps.auth import verify_api_key
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut
from app.models import Project
from app.crud import project as project_crud
from app.crud.base import get
from app.services.project_service import can_delete, create_project_with_places

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post(
    "",
    response_model=ProjectDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new travel project",
    description="Create a new travel project with places. Project must have at least 1 place and maximum 10 places.",
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Chicago Art Tour",
                        "description": "Exploring art museums in Chicago",
                        "start_date": "2024-06-01",
                        "completed": False,
                        "places": [
                            {
                                "id": 1,
                                "external_id": "27992",
                                "title": "A Sunday on La Grande Jatte",
                                "notes": "Must see - famous painting",
                                "visited": False,
                                "visited_at": None
                            }
                        ]
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Project must have at least 1 place"}
                }
            }
        },
        404: {
            "description": "Place not found in ArtIC API",
            "content": {
                "application/json": {
                    "example": {"detail": "Place with external_id '123' not found in ArtIC API. Please check the ID is valid."}
                }
            }
        }
    }
)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description, start_date=payload.start_date)
    
    # Project must have at least 1 place (requirement: minimum 1, maximum 10)
    if not payload.places:
        raise HTTPException(422, "Project must have at least 1 place")
    
    return await create_project_with_places(db, project, payload.places)

@router.get(
    "",
    response_model=list[ProjectOut],
    summary="List all travel projects",
    description="Get a paginated list of all travel projects. Returns projects ordered by ID (newest first).",
    responses={
        200: {
            "description": "List of projects",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Chicago Art Tour",
                            "description": "Exploring art museums",
                            "start_date": "2024-06-01",
                            "completed": False
                        },
                        {
                            "id": 2,
                            "name": "Paris Museums",
                            "description": None,
                            "start_date": None,
                            "completed": True
                        }
                    ]
                }
            }
        }
    }
)
def list_projects(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    db: Session = Depends(get_db)
):
    return project_crud.list_all(db, limit=min(limit, 100), offset=offset)

@router.get(
    "/{project_id}",
    response_model=ProjectDetailOut,
    summary="Get a single travel project",
    description="Get detailed information about a specific travel project including all its places.",
    responses={
        200: {
            "description": "Project details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Chicago Art Tour",
                        "description": "Exploring art museums",
                        "start_date": "2024-06-01",
                        "completed": False,
                        "places": [
                            {
                                "id": 1,
                                "external_id": "27992",
                                "title": "A Sunday on La Grande Jatte",
                                "notes": "Must see",
                                "visited": False,
                                "visited_at": None
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            }
        }
    }
)
def get_project(project_id: int = Path(..., description="ID of the project to retrieve"), db: Session = Depends(get_db)):
    project = get(db, Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project

@router.patch(
    "/{project_id}",
    response_model=ProjectDetailOut,
    summary="Update a travel project",
    description="Update project information (name, description, start_date). All fields are optional.",
    responses={
        200: {
            "description": "Project updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Updated Chicago Art Tour",
                        "description": "Updated description",
                        "start_date": "2024-07-01",
                        "completed": False,
                        "places": []
                    }
                }
            }
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            }
        }
    }
)
def update_project(
    project_id: int = Path(..., description="ID of the project to update"),
    payload: ProjectUpdate = ...,
    db: Session = Depends(get_db)
):
    project = get(db, Project, project_id)
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

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a travel project",
    description="Delete a travel project. Cannot delete if any place is marked as visited.",
    responses={
        204: {
            "description": "Project deleted successfully"
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project not found"}
                }
            }
        },
        409: {
            "description": "Cannot delete project with visited places",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot delete project with visited places"}
                }
            }
        }
    }
)
def delete_project(project_id: int = Path(..., description="ID of the project to delete"), db: Session = Depends(get_db)):
    project = get(db, Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not can_delete(project):
        raise HTTPException(409, "Cannot delete project with visited places")
    project_crud.delete(db, project)
    return None
