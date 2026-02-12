import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch
from app.main import create_app
from app.core.db import Base, init_db
from app.core.config import settings


# Тестова база даних в пам'яті
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Створює тестову базу даних для кожного тесту"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    
    # Імпортуємо моделі для створення таблиць
    from app.models import project, place  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Створює тестовий клієнт з підміною бази даних"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app = create_app()
    from app.deps.db import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_key():
    """Повертає валідний API ключ"""
    return settings.api_key


@pytest.fixture
def mock_artwork_response():
    """Мок відповіді від ArtIC API"""
    return {
        "data": {
            "id": 27992,
            "title": "A Sunday on La Grande Jatte",
            "artist_title": "Georges Seurat",
            "date_display": "1884-1886"
        }
    }


@pytest.fixture
def mock_get_artwork(mock_artwork_response):
    """Мок функції get_artwork з artic_service"""
    async def mock_artwork(external_id: str):
        # Повертаємо валідну відповідь для будь-якого external_id
        return {
            "id": int(external_id) if external_id.isdigit() else 27992,
            "title": f"Artwork {external_id}",
            "artist_title": "Test Artist",
            "date_display": "2024"
        }
    
    with patch("app.services.artic_service.get_artwork", side_effect=mock_artwork) as mock:
        yield mock
