import pytest
from datetime import date
from unittest.mock import AsyncMock, patch


@pytest.fixture
def project_data():
    """Тестові дані для проекту"""
    return {
        "name": "Test Project",
        "description": "Test Description",
        "start_date": "2024-06-01",
        "places": [
            {"external_id": "27992", "notes": "Test note 1"},
            {"external_id": "28560", "notes": "Test note 2"}
        ]
    }


def test_create_project_success(client, api_key, mock_get_artwork, project_data):
    """Тест успішного створення проекту"""
    response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["completed"] is False
    assert len(data["places"]) == 2
    mock_get_artwork.assert_called()


def test_create_project_no_places(client, api_key):
    """Тест створення проекту без місць"""
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "description": "Test Description",
            "places": []
        },
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert "at least 1 place" in response.json()["detail"]


def test_create_project_too_many_places(client, api_key, mock_get_artwork):
    """Тест створення проекту з більш ніж 10 місцями"""
    places = [{"external_id": "27992", "notes": f"Note {i}"} for i in range(11)]
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "places": places
        },
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert "1..10 places" in response.json()["detail"]


def test_create_project_duplicate_external_id(client, api_key, mock_get_artwork):
    """Тест створення проекту з дублікатами external_id"""
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "places": [
                {"external_id": "27992", "notes": "Note 1"},
                {"external_id": "27992", "notes": "Note 2"}
            ]
        },
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 409
    assert "Duplicate external_id" in response.json()["detail"]


def test_create_project_invalid_external_id(client, api_key, mock_get_artwork):
    """Тест створення проекту з невалідним external_id"""
    # Перевизначаємо мок для цього тесту
    async def return_none(external_id: str):
        return None
    
    with patch("app.services.artic_service.get_artwork", side_effect=return_none):
        response = client.post(
            "/projects",
            json={
                "name": "Test Project",
                "places": [{"external_id": "invalid", "notes": "Note"}]
            },
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404
        assert "not found in ArtIC API" in response.json()["detail"]


def test_list_projects_empty(client, api_key):
    """Тест отримання списку проектів (порожній список)"""
    response = client.get("/projects", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects_with_data(client, api_key, mock_get_artwork, project_data):
    """Тест отримання списку проектів з даними"""
    # Створюємо проект
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    assert create_response.status_code == 201
    
    # Отримуємо список
    response = client.get("/projects", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == project_data["name"]


def test_get_project_not_found(client, api_key):
    """Тест отримання неіснуючого проекту"""
    response = client.get("/projects/999", headers={"X-API-Key": api_key})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_project_success(client, api_key, mock_get_artwork, project_data):
    """Тест успішного отримання проекту"""
    # Створюємо проект
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    
    # Отримуємо проект
    response = client.get(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == project_data["name"]


def test_update_project_success(client, api_key, mock_get_artwork, project_data):
    """Тест успішного оновлення проекту"""
    # Створюємо проект
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    
    # Оновлюємо проект
    update_data = {
        "name": "Updated Project",
        "description": "Updated Description"
    }
    response = client.patch(
        f"/projects/{project_id}",
        json=update_data,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


def test_update_project_not_found(client, api_key):
    """Тест оновлення неіснуючого проекту"""
    response = client.patch(
        "/projects/999",
        json={"name": "Updated"},
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404


def test_delete_project_success(client, api_key, mock_get_artwork, project_data):
    """Тест успішного видалення проекту"""
    # Створюємо проект
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    
    # Видаляємо проект
    response = client.delete(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert response.status_code == 204
    
    # Перевіряємо, що проект видалено
    get_response = client.get(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert get_response.status_code == 404


def test_delete_project_with_visited_places(client, api_key, mock_get_artwork, project_data):
    """Тест видалення проекту з відвіданими місцями"""
    # Створюємо проект
    create_response = client.post(
        "/projects",
        json=project_data,
        headers={"X-API-Key": api_key}
    )
    project_id = create_response.json()["id"]
    place_id = create_response.json()["places"][0]["id"]
    
    # Позначаємо місце як відвідане
    client.patch(
        f"/projects/{project_id}/places/{place_id}",
        json={"visited": True},
        headers={"X-API-Key": api_key}
    )
    
    # Спробуємо видалити проект
    response = client.delete(f"/projects/{project_id}", headers={"X-API-Key": api_key})
    assert response.status_code == 409
    assert "visited places" in response.json()["detail"]


def test_delete_project_not_found(client, api_key):
    """Тест видалення неіснуючого проекту"""
    response = client.delete("/projects/999", headers={"X-API-Key": api_key})
    assert response.status_code == 404
