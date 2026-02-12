from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models import ProjectPlace


def list_for_project(db: Session, project_id: int, limit: int, offset: int) -> list[ProjectPlace]:
    stmt = (
        select(ProjectPlace)
        .where(ProjectPlace.project_id == project_id)
        .order_by(ProjectPlace.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())

def count_for_project(db: Session, project_id: int) -> int:
    stmt = select(func.count()).select_from(ProjectPlace).where(ProjectPlace.project_id == project_id)
    return int(db.scalar(stmt) or 0)

def exists_external(db: Session, project_id: int, external_id: str) -> bool:
    stmt = select(func.count()).select_from(ProjectPlace).where(
        ProjectPlace.project_id == project_id,
        ProjectPlace.external_id == external_id,
    )
    return (db.scalar(stmt) or 0) > 0
