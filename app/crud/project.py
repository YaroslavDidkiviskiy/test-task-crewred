from app.models.project import Project


from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Project

def create(db: Session, project: Project) -> Project:
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)

def list_all(db: Session, limit: int, offset: int) -> list[Project]:
    stmt = select(Project).order_by(Project.id.desc()).limit(limit).offset(offset)
    return list[Project](db.scalars(stmt).all())

def delete(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
