from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.project import Project
from app.crud.base import create, delete


def list_all(db: Session, limit: int, offset: int) -> list[Project]:
    stmt = select(Project).order_by(Project.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())
