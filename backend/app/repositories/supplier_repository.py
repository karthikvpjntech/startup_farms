import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.supplier import Supplier


class SupplierRepository:
    """Repository handling Supplier persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        supplier_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[Supplier]:
        stmt = select(Supplier).where(Supplier.id == supplier_id)
        if not include_deleted:
            stmt = stmt.where(Supplier.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, supplier_code: str) -> Optional[Supplier]:
        return db.scalar(select(Supplier).where(Supplier.supplier_code == supplier_code))

    @staticmethod
    def get_active_by_name_or_phone(
        db: Session,
        supplier_name: str,
        phone_number: str,
        exclude_id: Optional[uuid.UUID] = None
    ) -> Optional[Supplier]:
        stmt = select(Supplier).where(
            or_(
                func.lower(Supplier.supplier_name) == func.lower(supplier_name.strip()),
                Supplier.phone_number == phone_number.strip(),
            ),
            Supplier.is_deleted == False
        )
        if exclude_id is not None:
            stmt = stmt.where(Supplier.id != exclude_id)
        return db.scalar(stmt)

    @staticmethod
    def generate_next_supplier_code(db: Session) -> str:
        codes = db.scalars(select(Supplier.supplier_code)).all()
        max_num = 0
        pattern = re.compile(r"^SUP-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        return f"SUP-{max_num + 1:06d}"

    @staticmethod
    def create(
        db: Session,
        supplier_code: str,
        supplier_data: Dict[str, Any],
        created_by: uuid.UUID
    ) -> Supplier:
        supplier = Supplier(
            supplier_code=supplier_code,
            supplier_name=supplier_data["supplier_name"].strip(),
            contact_person=supplier_data.get("contact_person"),
            phone_number=supplier_data["phone_number"].strip(),
            email=supplier_data.get("email"),
            address_line1=supplier_data["address_line1"].strip(),
            address_line2=supplier_data.get("address_line2"),
            village_city=supplier_data["village_city"].strip(),
            district=supplier_data["district"].strip(),
            state=supplier_data["state"].strip(),
            pincode=supplier_data["pincode"].strip(),
            gstin=supplier_data.get("gstin"),
            supplier_type=supplier_data.get("supplier_type", "DISTRIBUTOR"),
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier

    @staticmethod
    def list_suppliers(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        supplier_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[Supplier]:
        stmt = select(Supplier)
        if not include_deleted:
            stmt = stmt.where(Supplier.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        if supplier_type:
            stmt = stmt.where(Supplier.supplier_type == supplier_type)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Supplier.supplier_name.ilike(term),
                    Supplier.supplier_code.ilike(term),
                    Supplier.phone_number.ilike(term),
                    Supplier.district.ilike(term),
                    Supplier.village_city.ilike(term),
                )
            )
        stmt = stmt.order_by(Supplier.supplier_name.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_suppliers(
        db: Session,
        search: Optional[str] = None,
        supplier_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        stmt = select(func.count(Supplier.id))
        if not include_deleted:
            stmt = stmt.where(Supplier.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        if supplier_type:
            stmt = stmt.where(Supplier.supplier_type == supplier_type)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Supplier.supplier_name.ilike(term),
                    Supplier.supplier_code.ilike(term),
                    Supplier.phone_number.ilike(term),
                    Supplier.district.ilike(term),
                    Supplier.village_city.ilike(term),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        supplier: Supplier,
        update_data: Dict[str, Any],
        updated_by: uuid.UUID
    ) -> Supplier:
        for field, value in update_data.items():
            if value is not None and hasattr(supplier, field):
                if isinstance(value, str):
                    value = value.strip()
                setattr(supplier, field, value)
        supplier.updated_by = updated_by
        supplier.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(supplier)
        return supplier

    @staticmethod
    def soft_delete(
        db: Session,
        supplier: Supplier,
        deleted_by: uuid.UUID
    ) -> Supplier:
        supplier.is_deleted = True
        supplier.is_active = False
        supplier.deleted_at = datetime.now(timezone.utc)
        supplier.deleted_by = deleted_by
        db.commit()
        db.refresh(supplier)
        return supplier

    @staticmethod
    def restore(
        db: Session,
        supplier: Supplier,
        restored_by: uuid.UUID
    ) -> Supplier:
        supplier.is_deleted = False
        supplier.is_active = True
        supplier.deleted_at = None
        supplier.deleted_by = None
        supplier.updated_by = restored_by
        supplier.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(supplier)
        return supplier
