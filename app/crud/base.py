from typing import TypeVar, Type
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


def create(db: Session, instance: ModelType) -> ModelType:
    """Створити новий запис"""
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def get(db: Session, model: Type[ModelType], id: int) -> ModelType | None:
    """Отримати запис за ID"""
    return db.get(model, id)


def delete(db: Session, instance: ModelType) -> None:
    """Видалити запис"""
    db.delete(instance)
    db.commit()
