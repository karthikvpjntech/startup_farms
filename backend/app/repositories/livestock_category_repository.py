import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.livestock import LivestockCategory, LivestockBreed


class LivestockCategoryRepository:
    """Repository handling Livestock Category and Breed master taxonomy operations."""

    @staticmethod
    def get_category_by_id(db: Session, category_id: uuid.UUID) -> Optional[LivestockCategory]:
        return db.scalar(select(LivestockCategory).where(LivestockCategory.id == category_id))

    @staticmethod
    def get_category_by_code(db: Session, code: str) -> Optional[LivestockCategory]:
        return db.scalar(select(LivestockCategory).where(LivestockCategory.code == code.strip().upper()))

    @staticmethod
    def list_categories(
        db: Session,
        is_active_only: bool = True
    ) -> List[LivestockCategory]:
        stmt = select(LivestockCategory)
        if is_active_only:
            stmt = stmt.where(LivestockCategory.is_active == True)
        stmt = stmt.order_by(LivestockCategory.display_order.asc(), LivestockCategory.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_category(db: Session, data: Dict[str, Any]) -> LivestockCategory:
        category = LivestockCategory(
            id=uuid.uuid4(),
            code=data["code"].strip().upper(),
            name=data["name"].strip(),
            name_ta=data.get("name_ta"),
            description=data.get("description"),
            icon_slug=data.get("icon_slug"),
            display_order=data.get("display_order", 0),
            is_active=data.get("is_active", True)
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def update_category(db: Session, category: LivestockCategory, data: Dict[str, Any]) -> LivestockCategory:
        for key, value in data.items():
            if value is not None and hasattr(category, key) and key != "id":
                if key == "code":
                    setattr(category, key, value.strip().upper())
                else:
                    setattr(category, key, value)
        db.commit()
        db.refresh(category)
        return category

    # Breed operations
    @staticmethod
    def get_breed_by_id(db: Session, breed_id: uuid.UUID) -> Optional[LivestockBreed]:
        return db.scalar(select(LivestockBreed).where(LivestockBreed.id == breed_id))

    @staticmethod
    def list_breeds(
        db: Session,
        category_id: Optional[uuid.UUID] = None,
        is_active_only: bool = True
    ) -> List[LivestockBreed]:
        stmt = select(LivestockBreed)
        if category_id is not None:
            stmt = stmt.where(LivestockBreed.category_id == category_id)
        if is_active_only:
            stmt = stmt.where(LivestockBreed.is_active == True)
        stmt = stmt.order_by(LivestockBreed.display_order.asc(), LivestockBreed.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_breed(db: Session, data: Dict[str, Any]) -> LivestockBreed:
        breed = LivestockBreed(
            id=uuid.uuid4(),
            category_id=data["category_id"],
            code=data["code"].strip().upper(),
            name=data["name"].strip(),
            name_ta=data.get("name_ta"),
            description=data.get("description"),
            characteristics=data.get("characteristics"),
            display_order=data.get("display_order", 0),
            is_active=data.get("is_active", True)
        )
        db.add(breed)
        db.commit()
        db.refresh(breed)
        return breed

    @staticmethod
    def update_breed(db: Session, breed: LivestockBreed, data: Dict[str, Any]) -> LivestockBreed:
        for key, value in data.items():
            if value is not None and hasattr(breed, key) and key != "id":
                if key == "code":
                    setattr(breed, key, value.strip().upper())
                else:
                    setattr(breed, key, value)
        db.commit()
        db.refresh(breed)
        return breed
