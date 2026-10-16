import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.procurement_request import ProcurementRequest


class ProcurementRequestRepository:
    """Repository handling ProcurementRequest database persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        request_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False
    ) -> Optional[ProcurementRequest]:
        """Retrieve procurement request by ID with optional farmer isolation and soft-delete filter."""
        stmt = select(ProcurementRequest).where(ProcurementRequest.id == request_id)
        if farmer_profile_id is not None:
            stmt = stmt.where(ProcurementRequest.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(ProcurementRequest.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, request_code: str) -> Optional[ProcurementRequest]:
        """Find procurement request by unique human-readable request_code."""
        return db.scalar(select(ProcurementRequest).where(ProcurementRequest.request_code == request_code))

    @staticmethod
    def generate_next_request_code(db: Session) -> str:
        """
        Generate a unique, monotonic procurement request code formatted as REQ-XXXXXX.
        Inspects existing codes in the database (including soft-deleted) to prevent code reuse.
        """
        codes = db.scalars(select(ProcurementRequest.request_code)).all()
        max_num = 0
        pattern = re.compile(r"^REQ-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"REQ-{next_num:06d}"

    @staticmethod
    def create(
        db: Session,
        farmer_profile_id: uuid.UUID,
        request_code: str,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> ProcurementRequest:
        """Create a new procurement request record linked to farmer profile."""
        procurement_req = ProcurementRequest(
            request_code=request_code,
            farmer_profile_id=farmer_profile_id,
            farm_id=data["farm_id"],
            input_id=data["input_id"],
            preferred_supplier_id=data.get("preferred_supplier_id"),
            quantity=Decimal(str(data["quantity"])),
            unit=data["unit"].strip(),
            required_date=data["required_date"],
            notes=data.get("notes"),
            status="PENDING",
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(procurement_req)
        db.commit()
        db.refresh(procurement_req)
        return procurement_req

    @staticmethod
    def list_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[ProcurementRequest]:
        """List procurement requests belonging to a farmer profile with pagination and search."""
        stmt = select(ProcurementRequest).where(ProcurementRequest.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(ProcurementRequest.is_deleted == False)
        if status:
            stmt = stmt.where(ProcurementRequest.status == status)
        if farm_id:
            stmt = stmt.where(ProcurementRequest.farm_id == farm_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ProcurementRequest.request_code.ilike(pattern),
                    ProcurementRequest.notes.ilike(pattern),
                )
            )
        stmt = stmt.order_by(ProcurementRequest.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        status: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count total procurement requests belonging to a farmer profile for pagination."""
        stmt = select(func.count(ProcurementRequest.id)).where(ProcurementRequest.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(ProcurementRequest.is_deleted == False)
        if status:
            stmt = stmt.where(ProcurementRequest.status == status)
        if farm_id:
            stmt = stmt.where(ProcurementRequest.farm_id == farm_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ProcurementRequest.request_code.ilike(pattern),
                    ProcurementRequest.notes.ilike(pattern),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[ProcurementRequest]:
        """List all procurement requests (for Admin)."""
        stmt = select(ProcurementRequest)
        if not include_deleted:
            stmt = stmt.where(ProcurementRequest.is_deleted == False)
        if status:
            stmt = stmt.where(ProcurementRequest.status == status)
        if farm_id:
            stmt = stmt.where(ProcurementRequest.farm_id == farm_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ProcurementRequest.request_code.ilike(pattern),
                    ProcurementRequest.notes.ilike(pattern),
                )
            )
        stmt = stmt.order_by(ProcurementRequest.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_all(
        db: Session,
        status: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count all procurement requests (for Admin)."""
        stmt = select(func.count(ProcurementRequest.id))
        if not include_deleted:
            stmt = stmt.where(ProcurementRequest.is_deleted == False)
        if status:
            stmt = stmt.where(ProcurementRequest.status == status)
        if farm_id:
            stmt = stmt.where(ProcurementRequest.farm_id == farm_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ProcurementRequest.request_code.ilike(pattern),
                    ProcurementRequest.notes.ilike(pattern),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        procurement_req: ProcurementRequest,
        update_data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> ProcurementRequest:
        """Update mutable fields of a pending procurement request."""
        now = datetime.now(timezone.utc)
        disallowed_fields = {
            "id", "request_code", "farmer_profile_id", "farm_id", "input_id",
            "created_at", "created_by", "is_deleted", "deleted_at", "deleted_by"
        }
        for key, value in update_data.items():
            if key not in disallowed_fields and hasattr(procurement_req, key) and value is not None:
                if key == "quantity":
                    setattr(procurement_req, key, Decimal(str(value)))
                else:
                    setattr(procurement_req, key, value)
        procurement_req.updated_by = updated_by
        procurement_req.updated_at = now
        db.commit()
        db.refresh(procurement_req)
        return procurement_req

    @staticmethod
    def update_status(
        db: Session,
        procurement_req: ProcurementRequest,
        status_value: str,
        updated_by: Optional[uuid.UUID] = None
    ) -> ProcurementRequest:
        """Update status of a procurement request."""
        procurement_req.status = status_value
        procurement_req.updated_by = updated_by
        procurement_req.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(procurement_req)
        return procurement_req

    @staticmethod
    def soft_delete(
        db: Session,
        procurement_req: ProcurementRequest,
        deleted_by: Optional[uuid.UUID] = None
    ) -> ProcurementRequest:
        """Soft-delete a procurement request."""
        now = datetime.now(timezone.utc)
        procurement_req.is_deleted = True
        procurement_req.deleted_at = now
        procurement_req.deleted_by = deleted_by
        procurement_req.updated_by = deleted_by
        procurement_req.updated_at = now
        db.commit()
        db.refresh(procurement_req)
        return procurement_req
