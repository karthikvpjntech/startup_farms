import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.role import Role


class RoleRepository:
    """Repository for Role database operations."""

    @staticmethod
    def get_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
        return db.scalar(select(Role).where(Role.id == role_id))

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Role]:
        return db.scalar(select(Role).where(Role.name == name))

    @staticmethod
    def get_all(db: Session) -> List[Role]:
        return list(db.scalars(select(Role)).all())

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Role:
        role = Role(
            name=name,
            description=description,
            is_active=is_active
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def get_by_names(db: Session, names: List[str]) -> List[Role]:
        if not names:
            return []
        return list(db.scalars(select(Role).where(Role.name.in_(names))).all())

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(select(func.count(Role.id))) or 0
