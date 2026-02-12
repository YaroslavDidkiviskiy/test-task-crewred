import pytest


def test_missing_api_key(client):
    """Тест запиту без API ключа"""
    response = client.get("/projects")
    assert response.status_code == 401
    assert "Missing API Key" in response.json()["detail"]


def test_invalid_api_key(client):
    """Тест запиту з невалідним API ключем"""
    response = client.get("/projects", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 403
    assert "Invalid API Key" in response.json()["detail"]


def test_valid_api_key(client, api_key):
    """Тест запиту з валідним API ключем"""
    response = client.get("/projects", headers={"X-API-Key": api_key})
    # Має повернути 200 (навіть якщо список порожній) або інший валідний статус
    assert response.status_code in [200, 404]  # 404 якщо немає роутера, але це не помилка авторизації
