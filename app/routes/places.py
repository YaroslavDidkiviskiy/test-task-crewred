from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from app.deps.db import get_db
from app.deps.auth import verify_api_key
from app.schemas import PlaceCreate, PlaceUpdate, PlaceOut
from app.crud import project as project_crud
from app.crud import place as place_crud
from app.services.project_service import add_place, update_place

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post(
    "/{project_id}/places",
    response_model=PlaceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a place to a project",
    description="Add a new place to an existing project. The place must exist in ArtIC API. Maximum 10 places per project.",
    responses={
        201: {
            "description": "Place added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "external_id": "27992",
                        "title": "A Sunday on La Grande Jatte",
                        "notes": "Must see - famous painting",
                        "visited": False,
                        "visited_at": None
                    }
                }
            }
        },
        404: {
            "description": "Project or place not found",
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {"detail": "Project not found"},
                        "place_not_found": {"detail": "Place with external_id '123' not found in ArtIC API. Please check the ID is valid."}
                    }
                }
            }
        },
        409: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "examples": {
                        "limit_reached": {"detail": "Project already has 10 places"},
                        "duplicate": {"detail": "Place already exists in this project"}
                    }
                }
            }
        }
    }
)
async def add_project_place(
    project_id: int = Path(..., description="ID of the project"),
    payload: PlaceCreate = ...,
    db: Session = Depends(get_db)
):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return await add_place(db, project, payload.external_id, payload.notes)

@router.get(
    "/{project_id}/places",
    response_model=list[PlaceOut],
    summary="List all places in a project",
    description="Get a paginated list of all places in a specific project.",
    responses={
        200: {
            "description": "List of places",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "external_id": "27992",
                            "title": "A Sunday on La Grande Jatte",
                            "notes": "Must see",
                            "visited": False,
                            "visited_at": None
                        },
                        {
                            "id": 2,
                            "external_id": "28560",
                            "title": "The Bedroom",
                            "notes": "Check hours",
                            "visited": True,
                            "visited_at": "2024-06-15T10:30:00"
                        }
                    ]
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
def list_project_places(
    project_id: int = Path(..., description="ID of the project"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of places to return"),
    offset: int = Query(0, ge=0, description="Number of places to skip"),
    db: Session = Depends(get_db)
):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return place_crud.list_for_project(db, project_id, limit=min(limit, 100), offset=offset)

@router.get(
    "/{project_id}/places/{place_id}",
    response_model=PlaceOut,
    summary="Get a single place",
    description="Get detailed information about a specific place in a project.",
    responses={
        200: {
            "description": "Place details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "external_id": "27992",
                        "title": "A Sunday on La Grande Jatte",
                        "notes": "Must see - famous painting",
                        "visited": False,
                        "visited_at": None
                    }
                }
            }
        },
        404: {
            "description": "Project or place not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Place not found"}
                }
            }
        }
    }
)
def get_project_place(
    project_id: int = Path(..., description="ID of the project"),
    place_id: int = Path(..., description="ID of the place"),
    db: Session = Depends(get_db)
):
    place = place_crud.get(db, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(404, "Place not found")
    return place

@router.patch(
    "/{project_id}/places/{place_id}",
    response_model=PlaceOut,
    summary="Update a place",
    description="Update place information (notes, visited status). When marked as visited, visited_at is automatically set.",
    responses={
        200: {
            "description": "Place updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "external_id": "27992",
                        "title": "A Sunday on La Grande Jatte",
                        "notes": "Visited on 2024-06-15. Amazing!",
                        "visited": True,
                        "visited_at": "2024-06-15T10:30:00"
                    }
                }
            }
        },
        404: {
            "description": "Project or place not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Place not found"}
                }
            }
        }
    }
)
def patch_project_place(
    project_id: int = Path(..., description="ID of the project"),
    place_id: int = Path(..., description="ID of the place"),
    payload: PlaceUpdate = ...,
    db: Session = Depends(get_db)
):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    place = place_crud.get(db, place_id)
    if not place or place.project_id != project_id:
        raise HTTPException(404, "Place not found")

    return update_place(db, project, place, payload.notes, payload.visited)
