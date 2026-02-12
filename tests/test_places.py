import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def project_with_place(client, api_key, mock_get_artwork):
    """Створює проект з одним місцем"""
    project_data = {
        "name": "Test Project",
        "description": "Test Description",
        "places": [{"external_id": "27992", "notes": "Test note"}]
    }
    response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project = response.json()
    return project["id"], project["places"][0]["id"]


def test_add_place_success(client, api_key, mock_get_artwork, project_with_place):
    """Тест успішного додавання місця до проекту"""
    project_id, _ = project_with_place
    
    response = client.post(
        f"/projects/{project_id}/places",
        json={"external_id": "28560", "notes": "New place"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["external_id"] == "28560"
    assert data["notes"] == "New place"
    assert data["visited"] is False


def test_add_place_project_not_found(client, api_key, mock_get_artwork):
    """Тест додавання місця до неіснуючого проекту"""
    response = client.post(
        "/projects/999/places",
        json={"external_id": "27992", "notes": "Test"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404


def test_add_place_duplicate_external_id(client, api_key, mock_get_artwork, project_with_place):
    """Тест додавання місця з дублікатом external_id"""
    project_id, _ = project_with_place
    
    response = client.post(
        f"/projects/{project_id}/places",
        json={"external_id": "27992", "notes": "Duplicate"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_add_place_max_limit(client, api_key, mock_get_artwork):
    """Тест додавання більше 10 місць до проекту"""
    # Створюємо проект з 10 місцями (використовуємо різні external_id)
    places = [{"external_id": str(27992 + i), "notes": f"Note {i}"} for i in range(10)]
    project_data = {
        "name": "Test Project",
        "places": places
    }
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    
    # Спробуємо додати 11-те місце
    response = client.post(
        f"/projects/{project_id}/places",
        json={"external_id": "28002", "notes": "11th place"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 409
    assert "10 places" in response.json()["detail"]


def test_add_place_invalid_external_id(client, api_key, project_with_place, mock_get_artwork):
    """Тест додавання місця з невалідним external_id"""
    project_id, _ = project_with_place
    
    # Перевизначаємо мок для цього тесту
    async def return_none(external_id: str):
        return None
    
    with patch("app.services.artic_service.get_artwork", side_effect=return_none):
        response = client.post(
            f"/projects/{project_id}/places",
            json={"external_id": "invalid", "notes": "Test"},
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404
        assert "not found in ArtIC API" in response.json()["detail"]


def test_list_places_success(client, api_key, mock_get_artwork, project_with_place):
    """Тест отримання списку місць проекту"""
    project_id, _ = project_with_place
    
    response = client.get(
        f"/projects/{project_id}/places",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_list_places_project_not_found(client, api_key):
    """Тест отримання списку місць неіснуючого проекту"""
    response = client.get("/projects/999/places", headers={"X-API-Key": api_key})
    assert response.status_code == 404


def test_get_place_success(client, api_key, mock_get_artwork, project_with_place):
    """Тест успішного отримання місця"""
    project_id, place_id = project_with_place
    
    response = client.get(
        f"/projects/{project_id}/places/{place_id}",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == place_id
    assert data["project_id"] == project_id


def test_get_place_not_found(client, api_key, project_with_place):
    """Тест отримання неіснуючого місця"""
    project_id, _ = project_with_place
    
    response = client.get(
        f"/projects/{project_id}/places/999",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404


def test_get_place_wrong_project(client, api_key, mock_get_artwork):
    """Тест отримання місця з неправильного проекту"""
    # Створюємо два проекти
    project1_data = {
        "name": "Project 1",
        "places": [{"external_id": "27992", "notes": "Place 1"}]
    }
    project2_data = {
        "name": "Project 2",
        "places": [{"external_id": "27992", "notes": "Place 2"}]
    }
    
    response1 = client.post("/projects", json=project1_data, headers={"X-API-Key": api_key})
    response2 = client.post("/projects", json=project2_data, headers={"X-API-Key": api_key})
    
    project1_id = response1.json()["id"]
    project2_id = response2.json()["id"]
    place2_id = response2.json()["places"][0]["id"]
    
    # Спробуємо отримати місце з project2 через project1
    response = client.get(
        f"/projects/{project1_id}/places/{place2_id}",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404


def test_update_place_notes(client, api_key, mock_get_artwork, project_with_place):
    """Тест оновлення нотаток місця"""
    project_id, place_id = project_with_place
    
    response = client.patch(
        f"/projects/{project_id}/places/{place_id}",
        json={"notes": "Updated notes"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated notes"
    assert data["visited"] is False


def test_update_place_mark_visited(client, api_key, mock_get_artwork, project_with_place):
    """Тест позначення місця як відвіданого"""
    project_id, place_id = project_with_place
    
    response = client.patch(
        f"/projects/{project_id}/places/{place_id}",
        json={"visited": True},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["visited"] is True
    assert data["visited_at"] is not None


def test_update_place_mark_unvisited(client, api_key, mock_get_artwork, project_with_place):
    """Тест зняття позначки відвіданого місця"""
    project_id, place_id = project_with_place
    
    # Спочатку позначимо як відвідане
    client.patch(
        f"/projects/{project_id}/places/{place_id}",
        json={"visited": True},
        headers={"X-API-Key": api_key}
    )
    
    # Потім знімемо позначку
    response = client.patch(
        f"/projects/{project_id}/places/{place_id}",
        json={"visited": False},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["visited"] is False
    assert data["visited_at"] is None


def test_update_place_completes_project(client, api_key, mock_get_artwork):
    """Тест що проект стає завершеним коли всі місця відвідані"""
    project_data = {
        "name": "Test Project",
        "places": [
            {"external_id": "27992", "notes": "Place 1"},
            {"external_id": "28560", "notes": "Place 2"}
        ]
    }
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    places = create_response.json()["places"]
    
    # Перевіряємо що проект не завершений
    get_response = client.get(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert get_response.json()["completed"] is False
    
    # Позначаємо всі місця як відвідані
    for place in places:
        client.patch(
            f"/projects/{project_id}/places/{place['id']}",
            json={"visited": True},
            headers={"X-API-Key": api_key}
        )
    
    # Перевіряємо що проект став завершеним
    get_response = client.get(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert get_response.json()["completed"] is True


def test_update_place_not_found(client, api_key, project_with_place):
    """Тест оновлення неіснуючого місця"""
    project_id, _ = project_with_place
    
    response = client.patch(
        f"/projects/{project_id}/places/999",
        json={"notes": "Updated"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404
