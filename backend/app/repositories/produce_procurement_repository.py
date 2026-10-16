import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.orm import Session, joinedload
from app.models.produce_procurement import ProduceProcurement
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun
from app.models.farmer_profile import FarmerProfile
from app.models.user import User


class ProduceProcurementRepository:
    """Data access repository for customer crop produce procurement entity."""

    @staticmethod
    def generate_request_code(db: Session) -> str:
        """Generates a sequential human-readable request code: PR-YYYYMM-XXXX."""
        now = datetime.now(timezone.utc)
        prefix = f"PR-{now.strftime('%Y%m')}-"
        query = select(func.count()).select_from(ProduceProcurement).where(
            ProduceProcurement.request_code.like(f"{prefix}%")
        )
        count = db.execute(query).scalar_one() + 1
        return f"{prefix}{count:04d}"

    @staticmethod
    def create(db: Session, procurement: ProduceProcurement) -> ProduceProcurement:
        db.add(procurement)
        db.commit()
        db.refresh(procurement)
        return procurement

    @staticmethod
    def get_by_id(
        db: Session,
        procurement_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        farmer_profile_id: Optional[uuid.UUID] = None
    ) -> Optional[ProduceProcurement]:
        query = select(ProduceProcurement).where(
            ProduceProcurement.id == procurement_id,
            ProduceProcurement.is_deleted.is_(False)
        )
        if customer_id:
            query = query.where(ProduceProcurement.customer_id == customer_id)
        if farmer_profile_id:
            query = query.where(ProduceProcurement.farmer_profile_id == farmer_profile_id)

        query = query.options(
            joinedload(ProduceProcurement.customer),
            joinedload(ProduceProcurement.farmer_profile).joinedload(FarmerProfile.user),
            joinedload(ProduceProcurement.farm),
            joinedload(ProduceProcurement.crop),
            joinedload(ProduceProcurement.cultivation),
            joinedload(ProduceProcurement.driver_user),
        )
        return db.execute(query).unique().scalar_one_or_none()

    @staticmethod
    def list_customer_procurements(
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[ProduceProcurement], int]:
        base_where = [
            ProduceProcurement.customer_id == customer_id,
            ProduceProcurement.is_deleted.is_(False)
        ]
        if status and status != 'ALL':
            base_where.append(ProduceProcurement.status == status)

        count_query = select(func.count(ProduceProcurement.id)).where(*base_where)
        total = db.execute(count_query).scalar_one()

        query = (
            select(ProduceProcurement)
            .where(*base_where)
            .options(
                joinedload(ProduceProcurement.customer),
                joinedload(ProduceProcurement.farmer_profile).joinedload(FarmerProfile.user),
                joinedload(ProduceProcurement.farm),
                joinedload(ProduceProcurement.crop),
                joinedload(ProduceProcurement.cultivation),
                joinedload(ProduceProcurement.driver_user),
            )
            .order_by(desc(ProduceProcurement.created_at))
            .offset(skip)
            .limit(limit)
        )
        items = list(db.execute(query).unique().scalars().all())
        return items, total

    @staticmethod
    def list_farmer_procurements(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[ProduceProcurement], int]:
        base_where = [
            ProduceProcurement.farmer_profile_id == farmer_profile_id,
            ProduceProcurement.is_deleted.is_(False)
        ]
        if status and status != 'ALL':
            base_where.append(ProduceProcurement.status == status)

        count_query = select(func.count(ProduceProcurement.id)).where(*base_where)
        total = db.execute(count_query).scalar_one()

        query = (
            select(ProduceProcurement)
            .where(*base_where)
            .options(
                joinedload(ProduceProcurement.customer),
                joinedload(ProduceProcurement.farmer_profile).joinedload(FarmerProfile.user),
                joinedload(ProduceProcurement.farm),
                joinedload(ProduceProcurement.crop),
                joinedload(ProduceProcurement.cultivation),
                joinedload(ProduceProcurement.driver_user),
            )
            .order_by(desc(ProduceProcurement.created_at))
            .offset(skip)
            .limit(limit)
        )
        items = list(db.execute(query).unique().scalars().all())
        return items, total

    @staticmethod
    def update(db: Session, procurement: ProduceProcurement) -> ProduceProcurement:
        procurement.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(procurement)
        return procurement

    @staticmethod
    def get_reserved_quantity_for_cultivation(db: Session, cultivation_id: uuid.UUID) -> Decimal:
        """Sums all quantities reserved in active/confirmed uncompleted procurements."""
        query = select(func.coalesce(func.sum(ProduceProcurement.requested_quantity), 0)).where(
            ProduceProcurement.cultivation_id == cultivation_id,
            ProduceProcurement.is_deleted.is_(False),
            ProduceProcurement.status.in_([
                "FARMER_CONFIRMED",
                "CONFIRMED",
                "PREPARING",
                "READY_FOR_DELIVERY",
                "OUT_FOR_DELIVERY"
            ])
        )
        val = db.execute(query).scalar_one()
        return Decimal(str(val))

    @staticmethod
    def get_reserved_quantity_for_farmer_crop(db: Session, farmer_profile_id: uuid.UUID, crop_id: uuid.UUID) -> Decimal:
        """Sums all quantities reserved for this farmer and crop."""
        query = select(func.coalesce(func.sum(ProduceProcurement.requested_quantity), 0)).where(
            ProduceProcurement.farmer_profile_id == farmer_profile_id,
            ProduceProcurement.crop_id == crop_id,
            ProduceProcurement.is_deleted.is_(False),
            ProduceProcurement.status.in_([
                "FARMER_CONFIRMED",
                "CONFIRMED",
                "PREPARING",
                "READY_FOR_DELIVERY",
                "OUT_FOR_DELIVERY"
            ])
        )
        val = db.execute(query).scalar_one()
        return Decimal(str(val))
