import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import Session
from app.models.shipment import (
    Shipment,
    ShipmentPackage,
    ShipmentTrackingEvent,
    DeliveryAttempt,
)
from app.models.transport_provider import TransportProvider
from app.models.pickup_request import PickupRequest


class ShipmentRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------
    # Shipment CRUD & Querying
    # -------------------------------------------------------------
    def create_shipment(self, shipment: Shipment) -> Shipment:
        self.db.add(shipment)
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def get_by_id(self, shipment_id: uuid.UUID) -> Optional[Shipment]:
        return self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        ).unique().scalar_one_or_none()

    def get_by_tracking_number(self, tracking_number: str) -> Optional[Shipment]:
        return self.db.execute(
            select(Shipment).where(
                func.upper(Shipment.tracking_number) == tracking_number.strip().upper()
            )
        ).unique().scalar_one_or_none()

    def get_by_shipment_number(self, shipment_number: str) -> Optional[Shipment]:
        return self.db.execute(
            select(Shipment).where(
                func.upper(Shipment.shipment_number) == shipment_number.strip().upper()
            )
        ).unique().scalar_one_or_none()

    def get_by_order_id(self, order_id: uuid.UUID) -> List[Shipment]:
        return list(
            self.db.execute(
                select(Shipment).where(Shipment.order_id == order_id)
            ).unique().scalars().all()
        )

    def list_farmer_shipments(
        self,
        farmer_profile_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Shipment], int]:
        query = select(Shipment).where(Shipment.farmer_profile_id == farmer_profile_id)

        if status:
            query = query.where(Shipment.current_status == status)

        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Shipment.shipment_number.ilike(s),
                    Shipment.tracking_number.ilike(s),
                    Shipment.destination_city.ilike(s),
                )
            )

        total_count = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar_one()

        items = list(
            self.db.execute(
                query.order_by(desc(Shipment.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).unique().scalars().all()
        )
        return items, total_count

    def list_admin_shipments(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        transport_provider_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[Shipment], int]:
        query = select(Shipment)

        if status:
            query = query.where(Shipment.current_status == status)

        if transport_provider_id:
            query = query.where(Shipment.transport_provider_id == transport_provider_id)

        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Shipment.shipment_number.ilike(s),
                    Shipment.tracking_number.ilike(s),
                    Shipment.origin_city.ilike(s),
                    Shipment.destination_city.ilike(s),
                )
            )

        total_count = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar_one()

        items = list(
            self.db.execute(
                query.order_by(desc(Shipment.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).unique().scalars().all()
        )
        return items, total_count

    def update_shipment(self, shipment: Shipment) -> Shipment:
        shipment.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    # -------------------------------------------------------------
    # Packages & Tracking Events
    # -------------------------------------------------------------
    def add_package(self, package: ShipmentPackage) -> ShipmentPackage:
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return package

    def add_tracking_event(self, event: ShipmentTrackingEvent) -> ShipmentTrackingEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def add_delivery_attempt(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    # -------------------------------------------------------------
    # Pickup Requests
    # -------------------------------------------------------------
    def create_pickup_request(self, pickup: PickupRequest) -> PickupRequest:
        self.db.add(pickup)
        self.db.commit()
        self.db.refresh(pickup)
        return pickup

    def get_pickup_request_by_id(self, pickup_id: uuid.UUID) -> Optional[PickupRequest]:
        return self.db.execute(
            select(PickupRequest).where(PickupRequest.id == pickup_id)
        ).unique().scalar_one_or_none()

    def get_pickup_by_code(self, pickup_code: str) -> Optional[PickupRequest]:
        return self.db.execute(
            select(PickupRequest).where(
                func.upper(PickupRequest.pickup_code) == pickup_code.strip().upper()
            )
        ).unique().scalar_one_or_none()

    def list_driver_pickups(
        self,
        driver_id: uuid.UUID,
        status: Optional[str] = None
    ) -> List[PickupRequest]:
        query = select(PickupRequest).where(PickupRequest.assigned_driver_id == driver_id)
        if status:
            query = query.where(PickupRequest.status == status)
        return list(
            self.db.execute(query.order_by(desc(PickupRequest.created_at))).unique().scalars().all()
        )

    def list_pending_pickups(self, page: int = 1, page_size: int = 20) -> Tuple[List[PickupRequest], int]:
        query = select(PickupRequest).where(PickupRequest.status == "PENDING")
        total_count = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar_one()
        items = list(
            self.db.execute(
                query.order_by(PickupRequest.scheduled_date.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).unique().scalars().all()
        )
        return items, total_count

    def update_pickup_request(self, pickup: PickupRequest) -> PickupRequest:
        pickup.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(pickup)
        return pickup

    # -------------------------------------------------------------
    # Transport Providers
    # -------------------------------------------------------------
    def create_transport_provider(self, provider: TransportProvider) -> TransportProvider:
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def get_transport_provider_by_id(self, provider_id: uuid.UUID) -> Optional[TransportProvider]:
        return self.db.execute(
            select(TransportProvider).where(TransportProvider.id == provider_id)
        ).unique().scalar_one_or_none()

    def get_transport_provider_by_code(self, provider_code: str) -> Optional[TransportProvider]:
        return self.db.execute(
            select(TransportProvider).where(
                func.upper(TransportProvider.provider_code) == provider_code.strip().upper()
            )
        ).unique().scalar_one_or_none()

    def list_transport_providers(self, active_only: bool = False) -> List[TransportProvider]:
        query = select(TransportProvider)
        if active_only:
            query = query.where(TransportProvider.is_active == True)
        return list(
            self.db.execute(query.order_by(TransportProvider.provider_name.asc())).unique().scalars().all()
        )

    def update_transport_provider(self, provider: TransportProvider) -> TransportProvider:
        provider.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    # -------------------------------------------------------------
    # Admin Stats & Counts
    # -------------------------------------------------------------
    def get_dashboard_stats(self) -> dict:
        total = self.db.execute(select(func.count(Shipment.id))).scalar_one() or 0
        created = self.db.execute(
            select(func.count(Shipment.id)).where(Shipment.current_status.in_(["CREATED", "READY_FOR_PICKUP", "PICKUP_ASSIGNED"]))
        ).scalar_one() or 0
        in_transit = self.db.execute(
            select(func.count(Shipment.id)).where(Shipment.current_status.in_(["PICKED_UP", "AT_ORIGIN_HUB", "IN_TRANSIT", "AT_DESTINATION_HUB"]))
        ).scalar_one() or 0
        out_for_delivery = self.db.execute(
            select(func.count(Shipment.id)).where(Shipment.current_status == "OUT_FOR_DELIVERY")
        ).scalar_one() or 0
        delivered = self.db.execute(
            select(func.count(Shipment.id)).where(Shipment.current_status == "DELIVERED")
        ).scalar_one() or 0
        failed_or_returned = self.db.execute(
            select(func.count(Shipment.id)).where(Shipment.current_status.in_(["DELIVERY_FAILED", "RETURN_INITIATED", "RETURN_IN_TRANSIT", "RETURNED"]))
        ).scalar_one() or 0
        pending_pickups = self.db.execute(
            select(func.count(PickupRequest.id)).where(PickupRequest.status == "PENDING")
        ).scalar_one() or 0
        active_providers = self.db.execute(
            select(func.count(TransportProvider.id)).where(TransportProvider.is_active == True)
        ).scalar_one() or 0

        return {
            "total_shipments": total,
            "created_count": created,
            "in_transit_count": in_transit,
            "out_for_delivery_count": out_for_delivery,
            "delivered_count": delivered,
            "failed_or_returned_count": failed_or_returned,
            "pending_pickups_count": pending_pickups,
            "active_providers_count": active_providers,
        }
