import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Project, ProjectPlace
from app.services.project_service import (
    recompute_completed,
    can_delete,
    create_project_with_places,
    add_place,
    update_place
)
from app.crud.base import create
from unittest.mock import AsyncMock, patch


def test_recompute_completed_no_places(test_db):
    """Тест перерахунку completed для проекту без місць"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    recompute_completed(project)
    assert project.completed is False


def test_recompute_completed_all_visited(test_db):
    """Тест перерахунку completed коли всі місця відвідані"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place1 = ProjectPlace(project_id=project.id, external_id="1", visited=True)
    place2 = ProjectPlace(project_id=project.id, external_id="2", visited=True)
    create(test_db, place1)
    create(test_db, place2)
    
    test_db.refresh(project)
    recompute_completed(project)
    assert project.completed is True


def test_recompute_completed_some_visited(test_db):
    """Тест перерахунку completed коли не всі місця відвідані"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place1 = ProjectPlace(project_id=project.id, external_id="1", visited=True)
    place2 = ProjectPlace(project_id=project.id, external_id="2", visited=False)
    create(test_db, place1)
    create(test_db, place2)
    
    test_db.refresh(project)
    recompute_completed(project)
    assert project.completed is False


def test_can_delete_no_visited_places(test_db):
    """Тест can_delete для проекту без відвіданих місць"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place1 = ProjectPlace(project_id=project.id, external_id="1", visited=False)
    place2 = ProjectPlace(project_id=project.id, external_id="2", visited=False)
    create(test_db, place1)
    create(test_db, place2)
    
    test_db.refresh(project)
    assert can_delete(project) is True


def test_can_delete_with_visited_places(test_db):
    """Тест can_delete для проекту з відвіданими місцями"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place1 = ProjectPlace(project_id=project.id, external_id="1", visited=True)
    place2 = ProjectPlace(project_id=project.id, external_id="2", visited=False)
    create(test_db, place1)
    create(test_db, place2)
    
    test_db.refresh(project)
    assert can_delete(project) is False


@pytest.mark.asyncio
async def test_create_project_with_places_success(test_db):
    """Тест успішного створення проекту з місцями"""
    project = Project(name="Test", description="Test")
    
    mock_artwork = {"id": 27992, "title": "Test Artwork"}
    
    with patch("app.services.project_service.get_artwork", new_callable=AsyncMock) as mock:
        mock.return_value = mock_artwork
        
        places_payload = [
            {"external_id": "27992", "notes": "Note 1"},
            {"external_id": "28560", "notes": "Note 2"}
        ]
        
        result = await create_project_with_places(test_db, project, places_payload)
        
        assert result is not None
        assert len(result.places) == 2
        assert result.places[0].external_id == "27992"
        assert result.places[0].title == "Test Artwork"
        assert result.places[1].external_id == "28560"
        assert result.places[1].title == "Test Artwork"


@pytest.mark.asyncio
async def test_create_project_with_places_no_places(test_db):
    """Тест створення проекту без місць"""
    project = Project(name="Test", description="Test")
    
    with pytest.raises(HTTPException) as exc_info:
        await create_project_with_places(test_db, project, [])
    
    assert exc_info.value.status_code == 422
    assert "at least 1 place" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_project_with_places_too_many(test_db):
    """Тест створення проекту з більш ніж 10 місцями"""
    project = Project(name="Test", description="Test")
    
    mock_artwork = {"id": 27992, "title": "Test Artwork"}
    
    async def mock_artwork_func(external_id: str):
        return mock_artwork
    
    with patch("app.services.project_service.get_artwork", side_effect=mock_artwork_func):
        places_payload = [{"external_id": str(27992 + i), "notes": f"Note {i}"} for i in range(11)]
        
        with pytest.raises(HTTPException) as exc_info:
            await create_project_with_places(test_db, project, places_payload)
        
        assert exc_info.value.status_code == 422
        assert "1..10 places" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_add_place_success(test_db):
    """Тест успішного додавання місця"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    mock_artwork = {"id": 27992, "title": "Test Artwork"}
    
    with patch("app.services.project_service.get_artwork", new_callable=AsyncMock) as mock:
        mock.return_value = mock_artwork
        
        place = await add_place(test_db, project, "27992", "Test notes")
        
        assert place is not None
        assert place.external_id == "27992"
        assert place.title == "Test Artwork"
        assert place.notes == "Test notes"
        assert place.visited is False


@pytest.mark.asyncio
async def test_add_place_invalid_external_id(test_db):
    """Тест додавання місця з невалідним external_id"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    with patch("app.services.project_service.get_artwork", new_callable=AsyncMock) as mock:
        mock.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await add_place(test_db, project, "invalid", "Test notes")
        
        assert exc_info.value.status_code == 404
        assert "not found in ArtIC API" in str(exc_info.value.detail)


def test_update_place_notes_only(test_db):
    """Тест оновлення тільки нотаток місця"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place = ProjectPlace(project_id=project.id, external_id="1", notes="Old notes")
    create(test_db, place)
    
    test_db.refresh(project)
    result = update_place(test_db, project, place, notes="New notes", visited=None)
    
    assert result.notes == "New notes"
    assert result.visited is False
    assert result.visited_at is None


def test_update_place_mark_visited(test_db):
    """Тест позначення місця як відвіданого"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place = ProjectPlace(project_id=project.id, external_id="1", visited=False)
    create(test_db, place)
    
    test_db.refresh(project)
    result = update_place(test_db, project, place, notes=None, visited=True)
    
    assert result.visited is True
    assert result.visited_at is not None
    assert isinstance(result.visited_at, datetime)


def test_update_place_mark_unvisited(test_db):
    """Тест зняття позначки відвіданого місця"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place = ProjectPlace(
        project_id=project.id,
        external_id="1",
        visited=True,
        visited_at=datetime.now(timezone.utc)
    )
    create(test_db, place)
    
    test_db.refresh(project)
    result = update_place(test_db, project, place, notes=None, visited=False)
    
    assert result.visited is False
    assert result.visited_at is None


def test_update_place_recomputes_completed(test_db):
    """Тест що update_place перераховує completed статус проекту"""
    project = Project(name="Test", description="Test")
    create(test_db, project)
    
    place1 = ProjectPlace(project_id=project.id, external_id="1", visited=False)
    place2 = ProjectPlace(project_id=project.id, external_id="2", visited=False)
    create(test_db, place1)
    create(test_db, place2)
    
    test_db.refresh(project)
    assert project.completed is False
    
    # Позначаємо обидва місця як відвідані
    update_place(test_db, project, place1, notes=None, visited=True)
    test_db.refresh(project)
    assert project.completed is False  # Ще не всі
    
    update_place(test_db, project, place2, notes=None, visited=True)
    test_db.refresh(project)
    assert project.completed is True  # Всі відвідані
