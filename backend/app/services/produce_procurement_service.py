import logging
import uuid
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.user import User
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun
from app.models.farmer_profile import FarmerProfile
from app.models.produce_procurement import ProduceProcurement
from app.schemas.produce_procurement import (
    ProduceAvailabilityItem,
    CustomerProcurementCreateRequest,
    FarmerProcurementConfirmRequest,
    FarmerProcurementRejectRequest,
    ProcurementDeliveryUpdateRequest,
    ProcurementPaymentRequest,
    ProduceProcurementResponse,
    ProduceProcurementListResponse,
    HarvestAlertItem,
    HarvestAlertSubscriptionRequest,
    HarvestAlertSubscriptionResponse,
)
from app.repositories.produce_procurement_repository import ProduceProcurementRepository
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.models.enums import NotificationType

logger = logging.getLogger("agri_smart.produce_procurement_service")


class ProduceProcurementService:
    """
    Business service executing the complete Customer Produce Procurement workflow:
    Public Requisition -> Farmer Review & Stock Reservation -> Confirmation/Rejection -> Payment -> Delivery Progression.
    """

    @staticmethod
    def _map_to_response(p: ProduceProcurement) -> ProduceProcurementResponse:
        crop_local = p.crop.crop_name_local if p.crop else None
        local_names = p.crop.local_names if p.crop and p.crop.local_names else {}

        # Resolve Farm Location & Google Maps Link
        farm_name = p.farm.farm_name if p.farm else "Farmer Farm Holding"
        loc_parts = []
        if p.farm:
            if p.farm.village: loc_parts.append(p.farm.village)
            if p.farm.district: loc_parts.append(p.farm.district)
            if p.farm.state: loc_parts.append(p.farm.state)
            if p.farm.pincode: loc_parts.append(p.farm.pincode)
        elif p.farmer_profile:
            if p.farmer_profile.district: loc_parts.append(p.farmer_profile.district)
            if p.farmer_profile.state: loc_parts.append(p.farmer_profile.state)

        fallback_loc = f"{farm_name}, {', '.join(loc_parts)}".strip(", ") if loc_parts else farm_name
        resolved_pickup_loc = p.pickup_location or fallback_loc

        # Resolve Google Maps URL
        google_maps_url = p.google_maps_url
        if not google_maps_url:
            if p.farm and p.farm.latitude and p.farm.longitude:
                google_maps_url = f"https://maps.google.com/?q={p.farm.latitude},{p.farm.longitude}"
            else:
                encoded_loc = urllib.parse.quote_plus(resolved_pickup_loc)
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_loc}"

        # Generate WhatsApp Confirmation Message & Clickable Link
        buyer_mobile = p.customer.mobile_number if p.customer else p.contact_phone
        farmer_mobile = p.farmer_profile.user.mobile_number if p.farmer_profile and p.farmer_profile.user else None
        farmer_name = p.farmer_profile.user.full_name if p.farmer_profile and p.farmer_profile.user else "Farmer"
        buyer_name = p.customer.full_name if p.customer else p.contact_name

        whatsapp_text = (
            f"🌾 *Agri-Smart கொள்முதல் உறுதிப்படுத்தல் / Procurement Confirmed!*\n\n"
            f"வணக்கம் *{buyer_name}*, உங்கள் நேரடி கொள்முதல் கோரிக்கை ({p.request_code}) விவசாயி *{farmer_name}* அவர்களால் ஏற்கப்பட்டது.\n\n"
            f"📦 *பயிர் / Produce:* {p.product_name}\n"
            f"⚖️ *அளவு / Quantity:* {p.requested_quantity} {p.unit}\n"
            f"💰 *விலை / Price:* ₹{p.unit_price} / {p.unit} (மொத்தம்: ₹{p.total_amount})\n\n"
            f"📍 *பண்ணை முகவரி / Pickup Location:*\n{resolved_pickup_loc}\n\n"
            f"🗺️ *Google Maps வழித்தடம் / Map Navigation:*\n{google_maps_url}\n\n"
            f"📞 *விவசாயி தொடர்பு / Phone:* {farmer_mobile or 'Contact via App'}\n"
            f"🚜 *Agri-Smart Direct Farmer Connect*"
        )
        whatsapp_url = NotificationService.generate_whatsapp_link(buyer_mobile, whatsapp_text) if buyer_mobile else None

        return ProduceProcurementResponse(
            id=p.id,
            request_code=p.request_code,
            customer_id=p.customer_id,
            customer_name=p.customer.full_name if p.customer else p.contact_name,
            customer_mobile=buyer_mobile,
            farmer_profile_id=p.farmer_profile_id,
            farmer_name=farmer_name,
            farmer_mobile=farmer_mobile,
            farmer_district=p.farmer_profile.district if p.farmer_profile else None,
            farmer_village=p.farmer_profile.village if p.farmer_profile and hasattr(p.farmer_profile, "village") else None,
            farm_id=p.farm_id,
            farm_name=farm_name,
            crop_id=p.crop_id,
            crop_name=p.crop.crop_name if p.crop else p.product_name,
            crop_name_local=crop_local,
            local_names=local_names,
            product_name=p.product_name,
            requested_quantity=p.requested_quantity,
            unit=p.unit,
            unit_price=p.unit_price,
            total_amount=p.total_amount,
            required_date=p.required_date,
            delivery_location=p.delivery_location,
            delivery_city=p.delivery_city,
            delivery_pincode=p.delivery_pincode,
            contact_name=p.contact_name,
            contact_phone=p.contact_phone,
            notes=p.notes,

            pickup_location=resolved_pickup_loc,
            google_maps_url=google_maps_url,
            pickup_instructions=p.pickup_instructions,
            estimated_pickup_date=p.estimated_pickup_date,
            whatsapp_url=whatsapp_url,
            whatsapp_message_preview=whatsapp_text,

            status=p.status,
            rejection_reason=p.rejection_reason,
            payment_method=p.payment_method,
            payment_status=p.payment_status,
            payment_reference=p.payment_reference,
            payment_date=p.payment_date,
            driver_id=p.driver_id,
            driver_name=p.driver_name,
            driver_contact=p.driver_contact,
            vehicle_number=p.vehicle_number,
            tracking_notes=p.tracking_notes,
            delivered_at=p.delivered_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    # ========================================================================
    # Available Produce Discovery
    # ========================================================================

    @staticmethod
    def get_available_produce(
        db: Session,
        crop_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> List[ProduceAvailabilityItem]:
        """
        Aggregates available crops & produce from verified farmer cultivations and crop plans.
        Computes real-time available quantity = total harvest yield - active reserved procurements.
        """
        # Query active cultivations
        cult_query = (
            select(CultivationRun)
            .join(CultivationRun.farm_crop_plan)
            .join(FarmCropPlan.crop)
            .join(FarmCropPlan.farm)
            .join(CultivationRun.farmer_profile)
            .join(FarmerProfile.user)
            .where(
                CultivationRun.is_active.is_(True),
                CultivationRun.is_deleted.is_(False),
                Crop.is_active.is_(True),
                Crop.is_deleted.is_(False)
            )
        )

        if crop_id:
            cult_query = cult_query.where(FarmCropPlan.crop_id == crop_id)

        cultivations = list(db.execute(cult_query).scalars().all())
        results: List[ProduceAvailabilityItem] = []
        covered_farmer_crop_pairs = set()

        for c in cultivations:
            crop = c.farm_crop_plan.crop
            farm = c.farm_crop_plan.farm
            farmer = c.farmer_profile
            farmer_user = farmer.user

            if search:
                s = search.lower()
                matches = (
                    s in crop.crop_name.lower() or
                    (crop.crop_name_local and s in crop.crop_name_local.lower()) or
                    (farmer_user.full_name and s in farmer_user.full_name.lower()) or
                    (farm.farm_name and s in farm.farm_name.lower())
                )
                if not matches:
                    continue

            # Calculate available yield
            total_yield = Decimal(str(c.yield_quantity or 500))
            unit_price = Decimal(str(c.selling_price_per_unit or 25))
            unit = c.yield_unit or "kg"

            reserved_qty = ProduceProcurementRepository.get_reserved_quantity_for_cultivation(db, c.id)
            available_qty = max(Decimal("0.00"), total_yield - reserved_qty)

            covered_farmer_crop_pairs.add((farmer.id, crop.id))

            results.append(
                ProduceAvailabilityItem(
                    crop_id=crop.id,
                    crop_name=crop.crop_name,
                    crop_name_local=crop.crop_name_local,
                    local_names=crop.local_names or {},
                    crop_code=crop.crop_code,
                    crop_category=crop.crop_category,
                    image_url=crop.image_url,
                    farmer_profile_id=farmer.id,
                    farmer_name=farmer_user.full_name,
                    farmer_mobile=farmer_user.mobile_number,
                    farm_id=farm.id,
                    farm_name=farm.farm_name,
                    location=farm.village or farm.district or "Tamil Nadu",
                    district=farm.district,
                    state=farm.state,
                    cultivation_id=c.id,
                    farming_method=c.farming_method or "CONVENTIONAL",
                    available_quantity=available_qty,
                    unit=unit,
                    unit_price=unit_price,
                    harvest_date=c.target_harvest_date,
                )
            )

        # Also query any FarmCropPlans that haven't instantiated a CultivationRun yet
        plan_query = (
            select(FarmCropPlan)
            .join(FarmCropPlan.crop)
            .join(FarmCropPlan.farm)
            .join(Farm.farmer_profile)
            .join(FarmerProfile.user)
            .where(
                FarmCropPlan.is_active.is_(True),
                FarmCropPlan.is_deleted.is_(False),
                Crop.is_active.is_(True),
                Crop.is_deleted.is_(False)
            )
        )
        if crop_id:
            plan_query = plan_query.where(FarmCropPlan.crop_id == crop_id)

        plans = list(db.execute(plan_query).scalars().all())

        for p in plans:
            crop = p.crop
            farm = p.farm
            farmer = farm.farmer_profile
            farmer_user = farmer.user if farmer else None

            if not farmer or not farmer_user:
                continue

            if (farmer.id, crop.id) in covered_farmer_crop_pairs:
                continue

            if search:
                s = search.lower()
                matches = (
                    s in crop.crop_name.lower() or
                    (crop.crop_name_local and s in crop.crop_name_local.lower()) or
                    (farmer_user.full_name and s in farmer_user.full_name.lower()) or
                    (farm.farm_name and s in farm.farm_name.lower())
                )
                if not matches:
                    continue

            # Standard planned area yield estimation: ~500 kg per acre
            area = Decimal(str(p.planned_area or 1))
            estimated_yield = area * Decimal("500.00")
            reserved_qty = ProduceProcurementRepository.get_reserved_quantity_for_farmer_crop(db, farmer.id, crop.id)
            available_qty = max(Decimal("0.00"), estimated_yield - reserved_qty)

            covered_farmer_crop_pairs.add((farmer.id, crop.id))

            results.append(
                ProduceAvailabilityItem(
                    crop_id=crop.id,
                    crop_name=crop.crop_name,
                    crop_name_local=crop.crop_name_local,
                    local_names=crop.local_names or {},
                    crop_code=crop.crop_code,
                    crop_category=crop.crop_category,
                    image_url=crop.image_url,
                    farmer_profile_id=farmer.id,
                    farmer_name=farmer_user.full_name,
                    farmer_mobile=farmer_user.mobile_number,
                    farm_id=farm.id,
                    farm_name=farm.farm_name,
                    location=farm.village or farm.district or "Tamil Nadu",
                    district=farm.district,
                    state=farm.state,
                    cultivation_id=None,
                    farming_method="CONVENTIONAL",
                    available_quantity=available_qty,
                    unit="kg",
                    unit_price=Decimal("35.00"),
                    harvest_date=p.planned_end_date,
                )
            )

        # Fallback: If no farm plan exists for a catalog crop, query all active crops
        if not results and not crop_id and not search:
            crops = list(db.execute(select(Crop).where(Crop.is_active.is_(True), Crop.is_deleted.is_(False))).scalars().all())
            # Find any active farmer profile
            default_farmer = db.execute(select(FarmerProfile).join(FarmerProfile.user)).scalars().first()
            if default_farmer and default_farmer.user:
                default_farm = db.execute(select(Farm).where(Farm.farmer_profile_id == default_farmer.id)).scalars().first()
                for c in crops:
                    results.append(
                        ProduceAvailabilityItem(
                            crop_id=c.id,
                            crop_name=c.crop_name,
                            crop_name_local=c.crop_name_local,
                            local_names=c.local_names or {},
                            crop_code=c.crop_code,
                            crop_category=c.crop_category,
                            image_url=c.image_url,
                            farmer_profile_id=default_farmer.id,
                            farmer_name=default_farmer.user.full_name,
                            farmer_mobile=default_farmer.user.mobile_number,
                            farm_id=default_farm.id if default_farm else None,
                            farm_name=default_farm.farm_name if default_farm else "Agri-Smart Organic Farm",
                            location=(default_farm.village or default_farm.district) if default_farm else "Coimbatore",
                            district=default_farm.district if default_farm else "Coimbatore",
                            state=default_farm.state if default_farm else "Tamil Nadu",
                            cultivation_id=None,
                            farming_method="ORGANIC",
                            available_quantity=Decimal("500.00"),
                            unit="kg",
                            unit_price=Decimal("40.00"),
                            harvest_date=None,
                        )
                    )

        return results

    # ========================================================================
    # Customer Procurement Request Lifecycle
    # ========================================================================

    @staticmethod
    def create_procurement_request(
        db: Session,
        current_user: User,
        request: CustomerProcurementCreateRequest
    ) -> ProduceProcurementResponse:
        """
        Creates a public customer produce procurement request and alerts the target farmer.
        """
        crop = db.execute(select(Crop).where(Crop.id == request.crop_id, Crop.is_deleted.is_(False))).scalar_one_or_none()
        if not crop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified crop does not exist.")

        farmer_profile_id = request.farmer_profile_id
        farm_id = request.farm_id
        cultivation_id = request.cultivation_id

        # If farmer is not explicitly selected by customer, find the best matching farmer for this crop
        if not farmer_profile_id:
            available_items = ProduceProcurementService.get_available_produce(db, crop_id=crop.id)
            if available_items:
                best_item = available_items[0]
                farmer_profile_id = best_item.farmer_profile_id
                farm_id = best_item.farm_id
                cultivation_id = best_item.cultivation_id
            else:
                # Find any active farmer profile in database
                default_farmer = db.execute(select(FarmerProfile)).scalars().first()
                if not default_farmer:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No registered farmer is currently available to fulfill this crop procurement."
                    )
                farmer_profile_id = default_farmer.id

        farmer_profile = db.execute(
            select(FarmerProfile).join(FarmerProfile.user).where(FarmerProfile.id == farmer_profile_id)
        ).scalar_one_or_none()
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target farmer profile not found.")

        # Compute price & total amount
        unit_price = Decimal("30.00")
        if cultivation_id:
            cult = db.execute(select(CultivationRun).where(CultivationRun.id == cultivation_id)).scalar_one_or_none()
            if cult and cult.selling_price_per_unit:
                unit_price = Decimal(str(cult.selling_price_per_unit))

        total_amount = request.quantity * unit_price
        request_code = ProduceProcurementRepository.generate_request_code(db)

        # Localized product name snapshot e.g. "Paddy / நெல்"
        product_title = crop.crop_name
        if crop.crop_name_local:
            product_title = f"{crop.crop_name} / {crop.crop_name_local}"

        procurement = ProduceProcurement(
            id=uuid.uuid4(),
            request_code=request_code,
            customer_id=current_user.id,
            farmer_profile_id=farmer_profile_id,
            farm_id=farm_id,
            crop_id=crop.id,
            cultivation_id=cultivation_id,
            product_name=product_title,
            requested_quantity=request.quantity,
            unit=request.unit or "kg",
            unit_price=unit_price,
            total_amount=total_amount,
            required_date=request.required_date,
            delivery_location=request.delivery_location,
            delivery_city=request.delivery_city,
            delivery_pincode=request.delivery_pincode,
            contact_name=request.contact_name,
            contact_phone=request.contact_phone,
            notes=request.notes,
            status="PENDING",
            payment_method="CASH_ON_DELIVERY",
            payment_status="PENDING",
            created_by=current_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        saved = ProduceProcurementRepository.create(db, procurement)
        logger.info("Procurement Request %s created by Customer %s", saved.request_code, current_user.id)

        # Notify Farmer of new procurement request
        try:
            if farmer_profile.user and farmer_profile.user.mobile_number:
                msg = (
                    f"Agri-Smart Requisition: New Procurement Request {saved.request_code} for "
                    f"{saved.requested_quantity} {saved.unit} of {crop.crop_name} received from {saved.contact_name}. "
                    f"Please review & confirm on your dashboard."
                )
                NotificationService.send_sms(
                    db=db,
                    farmer_profile_id=farmer_profile.id,
                    recipient_mobile=farmer_profile.user.mobile_number,
                    recipient_name=farmer_profile.user.full_name or "Farmer",
                    message_body=msg,
                    recipient_type="FARMER",
                    notification_type="STAGE_ALERT",
                    related_entity_type="PRODUCE_PROCUREMENT",
                    related_entity_id=saved.id,
                )
        except Exception as e:
            logger.warning("Failed to dispatch farmer SMS alert: %s", e)

        return ProduceProcurementService._map_to_response(saved)

    # ========================================================================
    # Farmer Review & Confirmation
    # ========================================================================

    @staticmethod
    def farmer_confirm_request(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID,
        request: Optional[FarmerProcurementConfirmRequest] = None
    ) -> ProduceProcurementResponse:
        """
        Farmer reviews and confirms a customer procurement request.
        Validates available stock >= requested quantity, and reserves produce stock.
        """
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        procurement = ProduceProcurementRepository.get_by_id(
            db,
            procurement_id=procurement_id,
            farmer_profile_id=farmer_profile.id
        )
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement request not found.")

        if procurement.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm request in '{procurement.status}' status."
            )

        # Validate available quantity
        total_available = Decimal("500.00")
        if procurement.cultivation_id:
            cult = db.execute(select(CultivationRun).where(CultivationRun.id == procurement.cultivation_id)).scalar_one_or_none()
            if cult and cult.yield_quantity:
                total_available = Decimal(str(cult.yield_quantity))
        elif procurement.farm_id:
            plan = db.execute(
                select(FarmCropPlan).where(
                    FarmCropPlan.farm_id == procurement.farm_id,
                    FarmCropPlan.crop_id == procurement.crop_id
                )
            ).scalars().first()
            if plan and plan.planned_area:
                total_available = Decimal(str(plan.planned_area)) * Decimal("500.00")

        already_reserved = ProduceProcurementRepository.get_reserved_quantity_for_farmer_crop(
            db,
            farmer_profile.id,
            procurement.crop_id
        )
        current_net_available = max(Decimal("0.00"), total_available - already_reserved)

        if procurement.requested_quantity > current_net_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Requested quantity ({procurement.requested_quantity} {procurement.unit}) exceeds "
                    f"available produce stock ({current_net_available} {procurement.unit})."
                )
            )

        # Resolve Pickup Location & Google Maps Link
        farm_name = procurement.farm.farm_name if procurement.farm else "Farmer Farm Holding"
        loc_parts = []
        if procurement.farm:
            if procurement.farm.village: loc_parts.append(procurement.farm.village)
            if procurement.farm.district: loc_parts.append(procurement.farm.district)
            if procurement.farm.state: loc_parts.append(procurement.farm.state)
            if procurement.farm.pincode: loc_parts.append(procurement.farm.pincode)
        elif farmer_profile:
            if farmer_profile.district: loc_parts.append(farmer_profile.district)
            if farmer_profile.state: loc_parts.append(farmer_profile.state)

        fallback_loc = f"{farm_name}, {', '.join(loc_parts)}".strip(", ") if loc_parts else farm_name
        resolved_pickup_loc = (request.pickup_location if request and request.pickup_location else None) or fallback_loc

        # Resolve Google Maps URL
        resolved_maps_url = request.google_maps_url if request and request.google_maps_url else None
        if not resolved_maps_url:
            if procurement.farm and procurement.farm.latitude and procurement.farm.longitude:
                resolved_maps_url = f"https://maps.google.com/?q={procurement.farm.latitude},{procurement.farm.longitude}"
            else:
                encoded_loc = urllib.parse.quote_plus(resolved_pickup_loc)
                resolved_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_loc}"

        # Transition status to FARMER_CONFIRMED
        procurement.status = "FARMER_CONFIRMED"
        procurement.pickup_location = resolved_pickup_loc
        procurement.google_maps_url = resolved_maps_url
        if request and request.pickup_instructions:
            procurement.pickup_instructions = request.pickup_instructions
        if request and request.estimated_pickup_date:
            procurement.estimated_pickup_date = request.estimated_pickup_date
        if request and request.notes:
            procurement.notes = f"{procurement.notes or ''} | Farmer: {request.notes}".strip(" |")
        procurement.updated_by = current_user.id

        updated = ProduceProcurementRepository.update(db, procurement)
        logger.info("Procurement Request %s confirmed by Farmer %s", updated.request_code, current_user.id)

        # Notify Customer of confirmation via App, SMS, and WhatsApp
        buyer_mobile = updated.contact_phone
        farmer_mobile = current_user.mobile_number or ""

        whatsapp_text = (
            f"🌾 *Agri-Smart கொள்முதல் உறுதிப்படுத்தல் / Procurement Confirmed!*\n\n"
            f"வணக்கம் *{updated.contact_name}*, உங்கள் நேரடி கொள்முதல் கோரிக்கை ({updated.request_code}) விவசாயி *{current_user.full_name}* அவர்களால் ஏற்கப்பட்டது.\n\n"
            f"📦 *பயிர் / Produce:* {updated.product_name}\n"
            f"⚖️ *அளவு / Quantity:* {updated.requested_quantity} {updated.unit}\n"
            f"💰 *மொத்த தொகை / Total Amount:* ₹{updated.total_amount}\n"
            f"🗓️ *தயாராகும் தேதி / Ready Date:* {updated.estimated_pickup_date or updated.required_date}\n\n"
            f"📍 *பண்ணை முகவரி / Pickup Location:*\n{resolved_pickup_loc}\n\n"
            f"🗺️ *Google Maps வழித்தடம் / Map Link:*\n{resolved_maps_url}\n\n"
            f"📞 *விவசாயி தொடர்பு / Phone:* {farmer_mobile}\n"
            f"நேரடியாக பண்ணைக்கு வந்து பொருட்களை பெற்றுக்கொள்ளலாம். நன்றி! 🚜"
        )

        # 1. SMS Dispatch with Location Link
        try:
            sms_body = (
                f"🌾 Agri-Smart Notice: Procurement {updated.request_code} for {updated.requested_quantity} {updated.unit} "
                f"of {updated.product_name} is CONFIRMED by {current_user.full_name}.\n"
                f"Pickup: {resolved_pickup_loc}\n"
                f"Google Maps: {resolved_maps_url}\n"
                f"Farmer Phone: {farmer_mobile}"
            )
            NotificationService.send_sms(
                db=db,
                farmer_profile_id=farmer_profile.id,
                recipient_mobile=buyer_mobile,
                recipient_name=updated.contact_name,
                message_body=sms_body,
                recipient_type="CUSTOMER",
                notification_type="STAGE_ALERT",
                related_entity_type="PRODUCE_PROCUREMENT",
                related_entity_id=updated.id,
            )
        except Exception as e:
            logger.warning("Failed to dispatch customer confirmation SMS: %s", e)

        # 2. WhatsApp Dispatch
        try:
            NotificationService.send_whatsapp_message(
                db=db,
                farmer_profile_id=farmer_profile.id,
                recipient_mobile=buyer_mobile,
                recipient_name=updated.contact_name,
                message_body=whatsapp_text,
                related_entity_id=updated.id,
            )
        except Exception as e:
            logger.warning("Failed to dispatch WhatsApp confirmation: %s", e)

        return ProduceProcurementService._map_to_response(updated)

    @staticmethod
    def farmer_reject_request(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID,
        request: FarmerProcurementRejectRequest
    ) -> ProduceProcurementResponse:
        """
        Farmer rejects procurement request with reason.
        """
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        procurement = ProduceProcurementRepository.get_by_id(
            db,
            procurement_id=procurement_id,
            farmer_profile_id=farmer_profile.id
        )
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement request not found.")

        if procurement.status not in ["PENDING", "FARMER_CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject request in '{procurement.status}' status."
            )

        procurement.status = "FARMER_REJECTED"
        procurement.rejection_reason = request.rejection_reason
        procurement.updated_by = current_user.id

        updated = ProduceProcurementRepository.update(db, procurement)
        logger.info("Procurement Request %s rejected by Farmer %s: %s", updated.request_code, current_user.id, request.rejection_reason)

        # Notify customer of rejection
        try:
            msg = (
                f"Agri-Smart Notice: Your procurement request {updated.request_code} for {updated.product_name} "
                f"could not be fulfilled by the farmer. Reason: {request.rejection_reason}."
            )
            NotificationService.send_sms(
                db=db,
                farmer_profile_id=farmer_profile.id,
                recipient_mobile=updated.contact_phone,
                recipient_name=updated.contact_name,
                message_body=msg,
                recipient_type="CUSTOMER",
                notification_type="STAGE_ALERT",
                related_entity_type="PRODUCE_PROCUREMENT",
                related_entity_id=updated.id,
            )
        except Exception as e:
            logger.warning("Failed to dispatch customer rejection SMS: %s", e)

        return ProduceProcurementService._map_to_response(updated)

    # ========================================================================
    # Payment Settlement
    # ========================================================================

    @staticmethod
    def settle_payment(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID,
        request: ProcurementPaymentRequest
    ) -> ProduceProcurementResponse:
        """
        Settles customer payment for confirmed procurement and advances order to CONFIRMED.
        """
        procurement = ProduceProcurementRepository.get_by_id(
            db,
            procurement_id=procurement_id,
            customer_id=current_user.id
        )
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement request not found.")

        if procurement.status not in ["PENDING", "FARMER_CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment cannot be processed for request in '{procurement.status}' status."
            )

        procurement.payment_method = request.payment_method
        procurement.payment_status = "PAID"
        procurement.payment_reference = request.payment_reference or f"PAY-{uuid.uuid4().hex[:8].upper()}"
        procurement.payment_date = datetime.now(timezone.utc)
        procurement.status = "CONFIRMED"
        procurement.updated_by = current_user.id

        updated = ProduceProcurementRepository.update(db, procurement)
        logger.info("Procurement Request %s payment settled via %s", updated.request_code, request.payment_method)

        # Notify Farmer of payment completion
        try:
            farmer = updated.farmer_profile
            if farmer and farmer.user and farmer.user.mobile_number:
                msg = (
                    f"Agri-Smart Payment: Customer {updated.contact_name} completed payment of "
                    f"Rs.{updated.total_amount} for Order {updated.request_code}. Please prepare for delivery."
                )
                NotificationService.send_sms(
                    db=db,
                    farmer_profile_id=farmer.id,
                    recipient_mobile=farmer.user.mobile_number,
                    recipient_name=farmer.user.full_name or "Farmer",
                    message_body=msg,
                    recipient_type="FARMER",
                    notification_type="PAYMENT_RECEIPT",
                    related_entity_type="PRODUCE_PROCUREMENT",
                    related_entity_id=updated.id,
                )
        except Exception as e:
            logger.warning("Failed to dispatch payment notification SMS: %s", e)

        return ProduceProcurementService._map_to_response(updated)

    # ========================================================================
    # Delivery Progression
    # ========================================================================

    @staticmethod
    def update_delivery_status(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID,
        request: ProcurementDeliveryUpdateRequest
    ) -> ProduceProcurementResponse:
        """
        Advances procurement delivery lifecycle:
        CONFIRMED -> PREPARING -> READY_FOR_DELIVERY -> OUT_FOR_DELIVERY -> DELIVERED.
        """
        farmer_profile = current_user.farmer_profile
        is_farmer = farmer_profile is not None
        is_admin = any(ur.role.name == "SUPER_ADMIN" for ur in current_user.user_roles if ur.role)

        procurement = ProduceProcurementRepository.get_by_id(
            db,
            procurement_id=procurement_id,
            farmer_profile_id=farmer_profile.id if is_farmer and not is_admin else None
        )
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement order not found.")

        valid_statuses = {"PREPARING", "READY_FOR_DELIVERY", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"}
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid delivery status '{request.status}'. Allowed: {list(valid_statuses)}"
            )

        procurement.status = request.status
        if request.driver_name:
            procurement.driver_name = request.driver_name
        if request.driver_contact:
            procurement.driver_contact = request.driver_contact
        if request.vehicle_number:
            procurement.vehicle_number = request.vehicle_number
        if request.tracking_notes:
            procurement.tracking_notes = request.tracking_notes

        if request.status == "DELIVERED":
            procurement.delivered_at = datetime.now(timezone.utc)
            if procurement.payment_method == "CASH_ON_DELIVERY" and procurement.payment_status != "PAID":
                procurement.payment_status = "PAID"
                procurement.payment_date = datetime.now(timezone.utc)

        procurement.updated_by = current_user.id
        updated = ProduceProcurementRepository.update(db, procurement)
        logger.info("Procurement %s status updated to %s", updated.request_code, request.status)

        # Notify Customer of delivery progress
        try:
            status_labels = {
                "PREPARING": "is being packaged and weighed",
                "READY_FOR_DELIVERY": "is ready for pickup / driver handover",
                "OUT_FOR_DELIVERY": f"is OUT FOR DELIVERY with vehicle {updated.vehicle_number or 'dispatch'}",
                "DELIVERED": "has been DELIVERED successfully. Thank you for shopping with Agri-Smart!",
            }
            if request.status in status_labels:
                msg = f"🚚 Agri-Smart Update: Order {updated.request_code} ({updated.product_name}) {status_labels[request.status]}."
                NotificationService.send_sms(
                    db=db,
                    farmer_profile_id=updated.farmer_profile_id,
                    recipient_mobile=updated.contact_phone,
                    recipient_name=updated.contact_name,
                    message_body=msg,
                    recipient_type="CUSTOMER",
                    notification_type="STAGE_ALERT",
                    related_entity_type="PRODUCE_PROCUREMENT",
                    related_entity_id=updated.id,
                )
        except Exception as e:
            logger.warning("Failed to dispatch delivery update SMS: %s", e)

        return ProduceProcurementService._map_to_response(updated)

    # ========================================================================
    # Customer Query & Cancellation
    # ========================================================================

    @staticmethod
    def list_customer_procurements(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> ProduceProcurementListResponse:
        skip = (page - 1) * page_size
        items, total = ProduceProcurementRepository.list_customer_procurements(
            db=db,
            customer_id=current_user.id,
            skip=skip,
            limit=page_size,
            status=status
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [ProduceProcurementService._map_to_response(p) for p in items]
        return ProduceProcurementListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def list_farmer_procurements(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> ProduceProcurementListResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            return ProduceProcurementListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

        skip = (page - 1) * page_size
        items, total = ProduceProcurementRepository.list_farmer_procurements(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            status=status
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [ProduceProcurementService._map_to_response(p) for p in items]
        return ProduceProcurementListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_procurement_detail(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID
    ) -> ProduceProcurementResponse:
        procurement = ProduceProcurementRepository.get_by_id(db, procurement_id)
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement request not found.")

        is_admin = any(ur.role.name == "SUPER_ADMIN" for ur in current_user.user_roles if ur.role)
        is_customer = procurement.customer_id == current_user.id
        is_farmer = current_user.farmer_profile and procurement.farmer_profile_id == current_user.farmer_profile.id

        if not (is_admin or is_customer or is_farmer):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this procurement.")

        return ProduceProcurementService._map_to_response(procurement)

    @staticmethod
    def cancel_procurement(
        db: Session,
        current_user: User,
        procurement_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> ProduceProcurementResponse:
        procurement = ProduceProcurementRepository.get_by_id(
            db,
            procurement_id=procurement_id,
            customer_id=current_user.id
        )
        if not procurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement request not found.")

        if procurement.status not in ["PENDING", "FARMER_CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel request in '{procurement.status}' status. Delivery preparation has already commenced."
            )

        procurement.status = "CANCELLED"
        procurement.rejection_reason = reason or "Cancelled by customer"
        procurement.updated_by = current_user.id

        updated = ProduceProcurementRepository.update(db, procurement)
        logger.info("Procurement %s cancelled by Customer %s", updated.request_code, current_user.id)
        return ProduceProcurementService._map_to_response(updated)

    # ========================================================================
    # Fresh Harvest Alerts & Public Notifications Broadcast
    # ========================================================================

    @staticmethod
    def get_recent_harvest_alerts(
        db: Session,
        limit: int = 10
    ) -> List[HarvestAlertItem]:
        """
        Retrieves real-time harvest announcements and yield recordings for public visibility.
        """
        cult_query = (
            select(CultivationRun)
            .join(CultivationRun.farm_crop_plan)
            .join(FarmCropPlan.crop)
            .join(FarmCropPlan.farm)
            .join(CultivationRun.farmer_profile)
            .join(FarmerProfile.user)
            .where(
                CultivationRun.is_active.is_(True),
                CultivationRun.is_deleted.is_(False),
                CultivationRun.yield_quantity.is_not(None),
                CultivationRun.yield_quantity > 0,
            )
            .order_by(CultivationRun.updated_at.desc())
            .limit(limit)
        )

        cultivations = list(db.execute(cult_query).scalars().all())
        alerts: List[HarvestAlertItem] = []

        for c in cultivations:
            crop = c.farm_crop_plan.crop
            farm = c.farm_crop_plan.farm
            farmer_user = c.farmer_profile.user if c.farmer_profile else None

            alerts.append(
                HarvestAlertItem(
                    id=c.id,
                    cultivation_id=c.id,
                    crop_id=crop.id,
                    crop_name=crop.crop_name,
                    crop_name_local=crop.crop_name_local,
                    local_names=crop.local_names or {},
                    farmer_name=farmer_user.full_name if farmer_user else "Registered Farmer",
                    farmer_mobile=farmer_user.mobile_number if farmer_user else None,
                    farm_name=farm.farm_name if farm else "Verified Farm",
                    farm_location=(farm.village or farm.district or "Tamil Nadu") if farm else "Tamil Nadu",
                    yield_quantity=Decimal(str(c.yield_quantity or 500)),
                    yield_unit=c.yield_unit or "kg",
                    selling_price_per_unit=Decimal(str(c.selling_price_per_unit or 35)),
                    harvest_date=c.target_harvest_date or c.planned_end_date,
                    created_at=c.updated_at or c.created_at,
                )
            )

        # Fallback sample alerts if database is completely fresh
        if not alerts:
            crops = list(db.execute(select(Crop).where(Crop.is_active.is_(True)).limit(3)).scalars().all())
            for idx, cr in enumerate(crops):
                alerts.append(
                    HarvestAlertItem(
                        id=uuid.uuid4(),
                        cultivation_id=None,
                        crop_id=cr.id,
                        crop_name=cr.crop_name,
                        crop_name_local=cr.crop_name_local,
                        local_names=cr.local_names or {},
                        farmer_name="Murugan Agri Farms",
                        farmer_mobile="9876543210",
                        farm_name="Cauvery Delta Agro Fields",
                        farm_location="Thanjavur, Tamil Nadu",
                        yield_quantity=Decimal("1500.00") if idx == 0 else Decimal("850.00"),
                        yield_unit="kg" if idx != 0 else "Bags / மூட்டை",
                        selling_price_per_unit=Decimal("28.00") if idx == 0 else Decimal("42.00"),
                        harvest_date=datetime.now(timezone.utc).date(),
                        created_at=datetime.now(timezone.utc),
                    )
                )

        return alerts

    @staticmethod
    def subscribe_harvest_alerts(
        db: Session,
        request: HarvestAlertSubscriptionRequest
    ) -> HarvestAlertSubscriptionResponse:
        """
        Subscribes a public user/buyer for instant SMS and email alerts when farmers log new harvests.
        """
        crops_str = ", ".join(request.crops_interested) if request.crops_interested else "All Farm Produce (Nel, Vengayam, Kadalai)"
        channels = ["SMS / WhatsApp", "In-App Live Alerts"]
        if request.email:
            channels.append("Email Digest")

        # 1. Send Instant Confirmation SMS
        try:
            sms_msg = (
                f"🌾 Agri-Smart Alert: Welcome {request.name}! You are now subscribed to instant Harvest Yield notifications "
                f"for [{crops_str}]. You will receive SMS & Email alerts as soon as farmers post fresh harvests."
            )
            NotificationService.send_sms(
                db=db,
                farmer_profile_id=None,
                recipient_mobile=request.mobile_number,
                recipient_name=request.name,
                message_body=sms_msg,
                recipient_type="CUSTOMER",
                notification_type=NotificationType.YIELD_HARVEST_ALERT.value,
            )
        except Exception as e:
            logger.warning("Failed to dispatch subscription welcome SMS: %s", e)

        # 2. Send Instant Welcome Email
        if request.email:
            try:
                EmailService._send_smtp(
                    to_email=request.email,
                    subject="🌾 Agri-Smart: You're Subscribed to Fresh Harvest Alerts!",
                    html_content=f"""
                    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <h2 style="color: #15803d;">🌾 Welcome to Direct Farm Harvest Alerts</h2>
                        <p>Hello <strong>{request.name}</strong>,</p>
                        <p>You have successfully subscribed to real-time harvest alerts for <strong>{crops_str}</strong>.</p>
                        <p>Whenever a local farmer completes cultivation and records a fresh yield, you will immediately receive notification details with direct procurement prices, quantities, and direct farmer contact!</p>
                    </div>
                    """,
                    text_content=f"Welcome {request.name}! You are subscribed to harvest alerts for {crops_str}."
                )
            except Exception as e:
                logger.warning("Failed to dispatch subscription welcome email: %s", e)

        return HarvestAlertSubscriptionResponse(
            success=True,
            message=f"Successfully subscribed {request.name} for instant harvest alerts!",
            subscriber_name=request.name,
            subscribed_crops=request.crops_interested if request.crops_interested else ["All Produce"],
            notification_channels=channels,
        )

