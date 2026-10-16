import uuid
import secrets
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.enums import (
    ShipmentStatus,
    SpecialHandlingType,
    PackageType,
    PickupRequestStatus,
    PickupTimeWindow,
    DeliveryAttemptStatus,
    DeliveryFailureReason,
    MarketplaceOrderStatus,
)
from app.models.shipment import (
    Shipment,
    ShipmentPackage,
    ShipmentTrackingEvent,
    DeliveryAttempt,
)
from app.models.transport_provider import TransportProvider
from app.models.pickup_request import PickupRequest
from app.models.marketplace_order import MarketplaceOrder
from app.models.farmer_profile import FarmerProfile
from app.models.user import User
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentPackageCreate,
    ShipmentStatusUpdate,
    ShipmentAssignProvider,
    PickupRequestCreate,
    DeliveryAttemptCreate,
    TransportProviderCreate,
    TransportProviderUpdate,
    PublicTrackingResponse,
    ShipmentTrackingEventResponse,
)


class ShipmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShipmentRepository(db)

    # -------------------------------------------------------------
    # Identifier Generators
    # -------------------------------------------------------------
    @staticmethod
    def _generate_code(prefix: str, length: int = 5) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand = "".join([str(secrets.randbelow(10)) for _ in range(length)])
        return f"{prefix}-{date_str}-{rand}"

    @staticmethod
    def _generate_tracking_number() -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand = "".join([str(secrets.randbelow(10)) for _ in range(5)])
        return f"AGRI{date_str}{rand}"

    @staticmethod
    def _mask_name(name: Optional[str]) -> str:
        if not name:
            return "Customer"
        parts = name.strip().split()
        if len(parts) == 1:
            n = parts[0]
            if len(n) <= 2:
                return n[0] + "*"
            return n[0] + "***" + n[-1]
        first = parts[0]
        first_masked = (first[0] + "***" + first[-1]) if len(first) > 2 else first[0] + "*"
        last_initial = parts[-1][0].upper()
        return f"{first_masked} {last_initial}"

    # -------------------------------------------------------------
    # State Transition Rules
    # -------------------------------------------------------------
    VALID_TRANSITIONS: Dict[str, List[str]] = {
        ShipmentStatus.CREATED.value: [
            ShipmentStatus.READY_FOR_PICKUP.value,
            ShipmentStatus.PICKUP_ASSIGNED.value,
            ShipmentStatus.CANCELLED.value,
        ],
        ShipmentStatus.READY_FOR_PICKUP.value: [
            ShipmentStatus.PICKUP_ASSIGNED.value,
            ShipmentStatus.PICKED_UP.value,
            ShipmentStatus.CANCELLED.value,
        ],
        ShipmentStatus.PICKUP_ASSIGNED.value: [
            ShipmentStatus.PICKED_UP.value,
            ShipmentStatus.CANCELLED.value,
        ],
        ShipmentStatus.PICKED_UP.value: [
            ShipmentStatus.AT_ORIGIN_HUB.value,
            ShipmentStatus.IN_TRANSIT.value,
        ],
        ShipmentStatus.AT_ORIGIN_HUB.value: [
            ShipmentStatus.IN_TRANSIT.value,
            ShipmentStatus.AT_DESTINATION_HUB.value,
        ],
        ShipmentStatus.IN_TRANSIT.value: [
            ShipmentStatus.AT_DESTINATION_HUB.value,
            ShipmentStatus.OUT_FOR_DELIVERY.value,
        ],
        ShipmentStatus.AT_DESTINATION_HUB.value: [
            ShipmentStatus.OUT_FOR_DELIVERY.value,
        ],
        ShipmentStatus.OUT_FOR_DELIVERY.value: [
            ShipmentStatus.DELIVERED.value,
            ShipmentStatus.DELIVERY_FAILED.value,
        ],
        ShipmentStatus.DELIVERY_FAILED.value: [
            ShipmentStatus.OUT_FOR_DELIVERY.value,
            ShipmentStatus.RETURN_INITIATED.value,
        ],
        ShipmentStatus.RETURN_INITIATED.value: [
            ShipmentStatus.RETURN_IN_TRANSIT.value,
        ],
        ShipmentStatus.RETURN_IN_TRANSIT.value: [
            ShipmentStatus.RETURNED.value,
        ],
        ShipmentStatus.DELIVERED.value: [],
        ShipmentStatus.RETURNED.value: [],
        ShipmentStatus.CANCELLED.value: [],
    }

    # -------------------------------------------------------------
    # Farmer Operations
    # -------------------------------------------------------------
    def create_shipment(
        self,
        farmer_profile_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ShipmentCreate
    ) -> Shipment:
        # 1. Verify Order
        order = self.db.query(MarketplaceOrder).filter(MarketplaceOrder.id == data.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {data.order_id} not found."
            )
        if order.farmer_profile_id != farmer_profile_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create shipments for your own farm orders."
            )

        # 2. Check if active shipment already exists for this order
        existing = self.repo.get_by_order_id(order.id)
        active_shipments = [s for s in existing if s.current_status != ShipmentStatus.CANCELLED.value]
        if active_shipments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An active shipment ({active_shipments[0].shipment_number}) already exists for this order."
            )

        # 3. Generate Codes
        shipment_number = self._generate_code("SHP")
        tracking_number = self._generate_tracking_number()
        barcode_data = tracking_number
        qr_code_data = f"/tracking/{tracking_number}"

        # 4. Calculate packages & weights
        packages_data = data.packages
        if not packages_data:
            # Create default single package from order summary
            packages_data = [
                ShipmentPackageCreate(
                    item_description=f"Order #{order.order_number} Produce Items",
                    weight_kg=Decimal("2.50"),
                    package_type=PackageType.CORRUGATED_CARTON,
                )
            ]

        total_weight = sum([p.weight_kg for p in packages_data])
        initial_status = ShipmentStatus.READY_FOR_PICKUP.value if data.request_pickup else ShipmentStatus.CREATED.value

        # 5. Create Shipment
        shipment = Shipment(
            shipment_number=shipment_number,
            tracking_number=tracking_number,
            order_id=order.id,
            farmer_profile_id=farmer_profile_id,
            customer_id=order.customer_id,
            current_status=initial_status,
            current_location=f"{data.origin_city} (Farmer Hub)",
            origin_address=data.origin_address,
            origin_city=data.origin_city,
            origin_pincode=data.origin_pincode,
            destination_address=data.destination_address,
            destination_city=data.destination_city,
            destination_pincode=data.destination_pincode,
            total_packages=len(packages_data),
            total_weight_kg=total_weight,
            is_perishable=data.is_perishable,
            special_handling=data.special_handling.value,
            barcode_data=barcode_data,
            qr_code_data=qr_code_data,
            estimated_delivery_date=data.estimated_delivery_date or (date.today() + timedelta(days=3)),
        )
        created_shipment = self.repo.create_shipment(shipment)

        # 6. Add Packages
        for idx, pkg in enumerate(packages_data, start=1):
            pkg_num = f"PKG-{shipment_number.replace('SHP-', '')}-{idx}"
            package_obj = ShipmentPackage(
                shipment_id=created_shipment.id,
                package_number=pkg_num,
                package_barcode=pkg_num,
                item_description=pkg.item_description,
                weight_kg=pkg.weight_kg,
                package_type=pkg.package_type.value,
            )
            self.repo.add_package(package_obj)

        # 7. Initial Tracking Event
        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=created_shipment.id,
                status=initial_status,
                location_hub=f"{data.origin_city} Farm Gate",
                city=data.origin_city,
                remarks="Shipment generated by farmer. Produce packed and labeled.",
                updated_by_user_id=user_id,
                updated_by_role="FARMER",
            )
        )

        # 8. Create Pickup Request if requested
        if data.request_pickup:
            pickup_date = data.pickup_scheduled_date or date.today()
            pickup_code = self._generate_code("PKP")
            user = self.db.query(User).filter(User.id == user_id).first()
            contact_name = user.full_name if user else "Farmer"
            contact_phone = user.mobile_number if user else "9999999999"

            pickup = PickupRequest(
                pickup_code=pickup_code,
                shipment_id=created_shipment.id,
                farmer_profile_id=farmer_profile_id,
                pickup_address=data.origin_address,
                pickup_contact_name=contact_name,
                pickup_contact_phone=contact_phone,
                scheduled_date=pickup_date,
                time_window=data.pickup_time_window.value if data.pickup_time_window else PickupTimeWindow.MORNING_7_11.value,
                status=PickupRequestStatus.PENDING.value,
                notes="Automated pickup request upon shipment creation",
            )
            self.repo.create_pickup_request(pickup)

        # Update order status to READY_FOR_PICKUP if order was pending/confirmed
        if order.status in [MarketplaceOrderStatus.PENDING.value, MarketplaceOrderStatus.CONFIRMED.value, MarketplaceOrderStatus.FARMER_ACCEPTED.value]:
            order.status = MarketplaceOrderStatus.READY_FOR_PICKUP.value
            self.db.commit()

        self.db.expire_all()
        return self.get_shipment_by_id(created_shipment.id)

    def list_farmer_shipments(
        self,
        farmer_profile_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Shipment], int]:
        return self.repo.list_farmer_shipments(
            farmer_profile_id=farmer_profile_id,
            page=page,
            page_size=page_size,
            status=status,
            search=search,
        )

    def get_shipment_by_id(self, shipment_id: uuid.UUID) -> Shipment:
        shipment = self.repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found."
            )
        return shipment

    def request_pickup(
        self,
        shipment_id: uuid.UUID,
        farmer_profile_id: uuid.UUID,
        data: PickupRequestCreate,
    ) -> PickupRequest:
        shipment = self.get_shipment_by_id(shipment_id)
        if shipment.farmer_profile_id != farmer_profile_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this shipment."
            )

        pickup_code = self._generate_code("PKP")
        pickup = PickupRequest(
            pickup_code=pickup_code,
            shipment_id=shipment.id,
            farmer_profile_id=farmer_profile_id,
            pickup_address=data.pickup_address,
            pickup_contact_name=data.pickup_contact_name,
            pickup_contact_phone=data.pickup_contact_phone,
            scheduled_date=data.scheduled_date,
            time_window=data.time_window.value,
            status=PickupRequestStatus.PENDING.value,
            notes=data.notes,
        )
        created_pickup = self.repo.create_pickup_request(pickup)

        if shipment.current_status == ShipmentStatus.CREATED.value:
            shipment.current_status = ShipmentStatus.READY_FOR_PICKUP.value
            self.repo.update_shipment(shipment)

        return created_pickup

    # -------------------------------------------------------------
    # Driver & Logistics Scanning Operations
    # -------------------------------------------------------------
    def scan_code(self, raw_code: str) -> Dict[str, Any]:
        """
        Universal scan resolving tracking number, shipment number, package barcode, or pickup code.
        """
        clean_code = raw_code.strip()

        # 1. Try tracking number
        shipment = self.repo.get_by_tracking_number(clean_code)
        if shipment:
            return {"match_type": "TRACKING_NUMBER", "shipment": shipment}

        # 2. Try shipment number
        shipment = self.repo.get_by_shipment_number(clean_code)
        if shipment:
            return {"match_type": "SHIPMENT_NUMBER", "shipment": shipment}

        # 3. Try pickup code
        pickup = self.repo.get_pickup_by_code(clean_code)
        if pickup:
            shipment = self.repo.get_by_id(pickup.shipment_id)
            return {"match_type": "PICKUP_CODE", "pickup": pickup, "shipment": shipment}

        # 4. Try package barcode
        pkg = self.db.query(ShipmentPackage).filter(
            func.upper(ShipmentPackage.package_barcode) == clean_code.upper()
        ).first()
        if pkg:
            shipment = self.repo.get_by_id(pkg.shipment_id)
            return {"match_type": "PACKAGE_BARCODE", "package": pkg, "shipment": shipment}

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active shipment or package found matching code '{raw_code}'."
        )

    def confirm_pickup_by_driver(
        self,
        shipment_id: uuid.UUID,
        driver_id: uuid.UUID,
        location_hub: Optional[str] = None,
    ) -> Shipment:
        shipment = self.get_shipment_by_id(shipment_id)

        # Allow pickup from CREATED, READY_FOR_PICKUP, PICKUP_ASSIGNED
        allowed_statuses = [
            ShipmentStatus.CREATED.value,
            ShipmentStatus.READY_FOR_PICKUP.value,
            ShipmentStatus.PICKUP_ASSIGNED.value,
        ]
        if shipment.current_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm pickup for shipment currently in '{shipment.current_status}' state."
            )

        driver_user = self.db.query(User).filter(User.id == driver_id).first()
        driver_name = driver_user.full_name if driver_user else "Driver"

        shipment.current_status = ShipmentStatus.PICKED_UP.value
        shipment.driver_id = driver_id
        shipment.current_location = location_hub or f"{shipment.origin_city} (Picked up by {driver_name})"
        self.repo.update_shipment(shipment)

        # Update any pending/assigned pickup requests for this shipment
        for p in shipment.pickup_requests:
            if p.status in [PickupRequestStatus.PENDING.value, PickupRequestStatus.ASSIGNED.value]:
                p.status = PickupRequestStatus.COMPLETED.value
                p.assigned_driver_id = driver_id
                self.repo.update_pickup_request(p)

        # Add tracking event
        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=ShipmentStatus.PICKED_UP.value,
                location_hub=shipment.current_location,
                city=shipment.origin_city,
                remarks=f"Package physically verified and collected from farm by {driver_name}.",
                updated_by_user_id=driver_id,
                updated_by_role="DRIVER",
            )
        )

        self.db.commit()
        self.db.expire_all()
        return self.get_shipment_by_id(shipment.id)

    def update_shipment_status(
        self,
        shipment_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        update_data: ShipmentStatusUpdate,
    ) -> Shipment:
        shipment = self.get_shipment_by_id(shipment_id)
        current = shipment.current_status
        target = update_data.status.value

        # Validate status progression
        allowed = self.VALID_TRANSITIONS.get(current, [])
        # Super admin can override, but for regular flow enforce state machine
        if role != "SUPER_ADMIN" and target not in allowed and target != current:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current}' to '{target}'. Allowed next steps: {allowed}"
            )

        shipment.current_status = target
        if update_data.location_hub:
            shipment.current_location = update_data.location_hub

        self.repo.update_shipment(shipment)

        # Add event ledger entry
        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=target,
                location_hub=update_data.location_hub or shipment.current_location,
                city=update_data.city or shipment.destination_city,
                remarks=update_data.remarks,
                updated_by_user_id=user_id,
                updated_by_role=role,
            )
        )

        self.db.commit()
        self.db.expire_all()
        return self.get_shipment_by_id(shipment.id)

    def confirm_delivery(
        self,
        shipment_id: uuid.UUID,
        driver_id: uuid.UUID,
        data: DeliveryAttemptCreate,
    ) -> Shipment:
        shipment = self.get_shipment_by_id(shipment_id)

        shipment.current_status = ShipmentStatus.DELIVERED.value
        shipment.actual_delivery_date = datetime.now(timezone.utc)
        shipment.current_location = f"{shipment.destination_city} (Delivered to Customer)"
        self.repo.update_shipment(shipment)

        # Record successful attempt
        attempt = DeliveryAttempt(
            shipment_id=shipment.id,
            attempt_number=len(shipment.delivery_attempts) + 1,
            attempt_status=DeliveryAttemptStatus.SUCCESS.value,
            recipient_name=data.recipient_name or "Recipient",
            recipient_signature_note=data.recipient_signature_note,
            driver_notes=data.driver_notes,
        )
        self.repo.add_delivery_attempt(attempt)

        # Add tracking milestone
        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=ShipmentStatus.DELIVERED.value,
                location_hub=shipment.destination_address,
                city=shipment.destination_city,
                remarks=f"Delivered successfully to {data.recipient_name or 'customer'}.",
                updated_by_user_id=driver_id,
                updated_by_role="DRIVER",
            )
        )

        # Update order status
        order = self.db.query(MarketplaceOrder).filter(MarketplaceOrder.id == shipment.order_id).first()
        if order:
            order.status = MarketplaceOrderStatus.DELIVERED.value
            self.db.commit()

        self.db.expire_all()
        return self.get_shipment_by_id(shipment.id)

    def record_delivery_failure(
        self,
        shipment_id: uuid.UUID,
        driver_id: uuid.UUID,
        data: DeliveryAttemptCreate,
    ) -> Shipment:
        shipment = self.get_shipment_by_id(shipment_id)

        target_status = ShipmentStatus.DELIVERY_FAILED.value
        failure_reason = data.failure_reason.value if data.failure_reason else DeliveryFailureReason.OTHER.value

        shipment.current_status = target_status
        shipment.current_location = f"{shipment.destination_city} (Delivery Attempt Failed: {failure_reason})"
        self.repo.update_shipment(shipment)

        # Record failed attempt
        attempt = DeliveryAttempt(
            shipment_id=shipment.id,
            attempt_number=len(shipment.delivery_attempts) + 1,
            attempt_status=DeliveryAttemptStatus.FAILED.value,
            failure_reason=failure_reason,
            driver_notes=data.driver_notes,
        )
        self.repo.add_delivery_attempt(attempt)

        # Add event
        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=target_status,
                location_hub=shipment.destination_city,
                city=shipment.destination_city,
                remarks=f"Delivery attempt failed. Reason: {failure_reason}. Note: {data.driver_notes or 'None'}",
                updated_by_user_id=driver_id,
                updated_by_role="DRIVER",
            )
        )

        self.db.commit()
        self.db.expire_all()
        return self.get_shipment_by_id(shipment.id)

    # -------------------------------------------------------------
    # Public Tracking & Privacy
    # -------------------------------------------------------------
    def get_public_tracking(self, tracking_number: str) -> PublicTrackingResponse:
        shipment = self.repo.get_by_tracking_number(tracking_number)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tracking number '{tracking_number}' was not found in Agri-Smart network."
            )

        customer_name = shipment.customer.full_name if shipment.customer else "Customer"
        masked_name = self._mask_name(customer_name)

        tracking_events = [
            ShipmentTrackingEventResponse.model_validate(e)
            for e in sorted(shipment.tracking_events, key=lambda x: x.event_timestamp)
        ]

        return PublicTrackingResponse(
            tracking_number=shipment.tracking_number,
            shipment_number=shipment.shipment_number,
            current_status=shipment.current_status,
            current_location=shipment.current_location,
            origin_city=shipment.origin_city,
            origin_pincode=shipment.origin_pincode,
            destination_city=shipment.destination_city,
            destination_pincode=shipment.destination_pincode,
            masked_customer_name=masked_name,
            total_packages=shipment.total_packages,
            total_weight_kg=shipment.total_weight_kg,
            is_perishable=shipment.is_perishable,
            special_handling=shipment.special_handling,
            estimated_delivery_date=shipment.estimated_delivery_date,
            actual_delivery_date=shipment.actual_delivery_date,
            created_at=shipment.created_at,
            tracking_events=tracking_events,
        )

    # -------------------------------------------------------------
    # Transport Providers & Admin Hub
    # -------------------------------------------------------------
    def list_admin_shipments(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        transport_provider_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[Shipment], int]:
        return self.repo.list_admin_shipments(
            page=page,
            page_size=page_size,
            status=status,
            search=search,
            transport_provider_id=transport_provider_id,
        )

    def get_admin_dashboard_stats(self) -> dict:
        return self.repo.get_dashboard_stats()

    def create_transport_provider(self, data: TransportProviderCreate) -> TransportProvider:
        existing = self.repo.get_transport_provider_by_code(data.provider_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transport Provider with code '{data.provider_code}' already exists."
            )

        provider = TransportProvider(
            provider_name=data.provider_name,
            provider_code=data.provider_code.upper().strip(),
            contact_person=data.contact_person,
            phone_number=data.phone_number,
            email=data.email,
            vehicle_type=data.vehicle_type,
            vehicle_number=data.vehicle_number,
            service_areas=data.service_areas,
            is_active=data.is_active,
        )
        return self.repo.create_transport_provider(provider)

    def list_transport_providers(self, active_only: bool = False) -> List[TransportProvider]:
        return self.repo.list_transport_providers(active_only=active_only)

    def update_transport_provider(
        self,
        provider_id: uuid.UUID,
        data: TransportProviderUpdate,
    ) -> TransportProvider:
        provider = self.repo.get_transport_provider_by_id(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transport Provider {provider_id} not found."
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(provider, field, value)

        return self.repo.update_transport_provider(provider)

    def assign_shipment_provider(
        self,
        shipment_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ShipmentAssignProvider,
    ) -> Shipment:
        shipment = self.get_shipment_by_id(shipment_id)

        if data.transport_provider_id:
            provider = self.repo.get_transport_provider_by_id(data.transport_provider_id)
            if not provider:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transport Provider not found."
                )
            shipment.transport_provider_id = data.transport_provider_id

        if data.driver_id:
            driver = self.db.query(User).filter(User.id == data.driver_id).first()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Driver user not found."
                )
            shipment.driver_id = data.driver_id

        if data.estimated_delivery_date:
            shipment.estimated_delivery_date = data.estimated_delivery_date

        if shipment.current_status in [ShipmentStatus.CREATED.value, ShipmentStatus.READY_FOR_PICKUP.value]:
            shipment.current_status = ShipmentStatus.PICKUP_ASSIGNED.value

        self.repo.update_shipment(shipment)

        # Also update linked pickup request
        for p in shipment.pickup_requests:
            if p.status == PickupRequestStatus.PENDING.value and data.driver_id:
                p.status = PickupRequestStatus.ASSIGNED.value
                p.assigned_driver_id = data.driver_id
                self.repo.update_pickup_request(p)

        self.repo.add_tracking_event(
            ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=shipment.current_status,
                location_hub=shipment.origin_city,
                city=shipment.origin_city,
                remarks="Assigned to transport carrier/driver.",
                updated_by_user_id=user_id,
                updated_by_role="SUPER_ADMIN",
            )
        )

        return shipment
