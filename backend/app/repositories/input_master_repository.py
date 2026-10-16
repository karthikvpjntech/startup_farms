import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.input_master import InputMaster


class InputMasterRepository:
    """Repository handling InputMaster persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        input_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[InputMaster]:
        stmt = select(InputMaster).where(InputMaster.id == input_id)
        if not include_deleted:
            stmt = stmt.where(InputMaster.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, input_code: str) -> Optional[InputMaster]:
        return db.scalar(select(InputMaster).where(InputMaster.input_code == input_code))

    @staticmethod
    def get_active_by_name(
        db: Session,
        input_name: str,
        exclude_id: Optional[uuid.UUID] = None
    ) -> Optional[InputMaster]:
        clean_name = input_name.strip()
        stmt = select(InputMaster).where(
            func.lower(InputMaster.input_name) == func.lower(clean_name),
            InputMaster.is_deleted == False
        )
        if exclude_id is not None:
            stmt = stmt.where(InputMaster.id != exclude_id)
        return db.scalar(stmt)

    @staticmethod
    def generate_next_input_code(db: Session) -> str:
        codes = db.scalars(select(InputMaster.input_code)).all()
        max_num = 0
        pattern = re.compile(r"^INP-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        return f"INP-{max_num + 1:06d}"

    @staticmethod
    def create(
        db: Session,
        input_code: str,
        input_data: Dict[str, Any],
        created_by: uuid.UUID
    ) -> InputMaster:
        input_item = InputMaster(
            input_code=input_code,
            input_name=input_data["input_name"].strip(),
            category=input_data["category"],
            unit=input_data["unit"],
            technical_name=input_data.get("technical_name"),
            brand_name=input_data.get("brand_name"),
            description=input_data.get("description"),
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(input_item)
        db.commit()
        db.refresh(input_item)
        return input_item

    @staticmethod
    def list_inputs(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[InputMaster]:
        stmt = select(InputMaster)
        if not include_deleted:
            stmt = stmt.where(InputMaster.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(InputMaster.is_active == is_active)
        if category:
            stmt = stmt.where(InputMaster.category == category)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    InputMaster.input_name.ilike(term),
                    InputMaster.input_code.ilike(term),
                    InputMaster.technical_name.ilike(term),
                    InputMaster.brand_name.ilike(term),
                )
            )
        stmt = stmt.order_by(InputMaster.input_name.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_inputs(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        stmt = select(func.count(InputMaster.id))
        if not include_deleted:
            stmt = stmt.where(InputMaster.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(InputMaster.is_active == is_active)
        if category:
            stmt = stmt.where(InputMaster.category == category)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    InputMaster.input_name.ilike(term),
                    InputMaster.input_code.ilike(term),
                    InputMaster.technical_name.ilike(term),
                    InputMaster.brand_name.ilike(term),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        input_item: InputMaster,
        update_data: Dict[str, Any],
        updated_by: uuid.UUID
    ) -> InputMaster:
        for field, value in update_data.items():
            if value is not None and hasattr(input_item, field):
                if isinstance(value, str):
                    value = value.strip()
                setattr(input_item, field, value)
        input_item.updated_by = updated_by
        input_item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(input_item)
        return input_item

    @staticmethod
    def soft_delete(
        db: Session,
        input_item: InputMaster,
        deleted_by: uuid.UUID
    ) -> InputMaster:
        input_item.is_deleted = True
        input_item.is_active = False
        input_item.deleted_at = datetime.now(timezone.utc)
        input_item.deleted_by = deleted_by
        db.commit()
        db.refresh(input_item)
        return input_item
