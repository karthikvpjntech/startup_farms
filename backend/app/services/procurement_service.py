import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.input_master_repository import InputMasterRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.procurement_request_repository import ProcurementRequestRepository
from app.schemas.procurement_request import (
    ProcurementRequestCreate,
    ProcurementRequestUpdate,
    ProcurementRequestStatusUpdate,
    ProcurementRequestResponse,
    ProcurementListResponse,
)

logger = logging.getLogger("agri_smart.procurement_service")


class ProcurementService:
    """Service handling Procurement Request creation, farmer listing, cancellation, and admin approval."""

    @staticmethod
    def _resolve_farmer_profile(db: Session, current_user: User) -> FarmerProfile:
        """
        Validates that the authenticated user possesses the FARMER role and has completed their FarmerProfile.
        """
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.FARMER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the FARMER role"
            )

        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Farmer profile must be completed before submitting procurement requests"
            )
        return profile

    @staticmethod
    def create_procurement(
        db: Session,
        current_user: User,
        request: ProcurementRequestCreate
    ) -> ProcurementRequestResponse:
        """Creates a new procurement request for a farm and catalog input."""
        farmer_profile = ProcurementService._resolve_farmer_profile(db, current_user)

        # Verify farm parcel belongs to this farmer
        farm = FarmRepository.get_by_id(db, request.farm_id, farmer_profile_id=farmer_profile.id)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified farm parcel was not found or does not belong to the current farmer"
            )

        # Verify input item exists and is active
        input_item = InputMasterRepository.get_by_id(db, request.input_id)
        if not input_item or not input_item.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified agricultural input item is inactive or does not exist in catalog"
            )

        # Verify supplier if preferred_supplier_id is specified
        if request.preferred_supplier_id:
            supplier = SupplierRepository.get_by_id(db, request.preferred_supplier_id)
            if not supplier or not supplier.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified preferred supplier is inactive or does not exist"
                )

        request_code = ProcurementRequestRepository.generate_next_request_code(db)
        procurement_req = ProcurementRequestRepository.create(
            db=db,
            farmer_profile_id=farmer_profile.id,
            request_code=request_code,
            data=request.model_dump(),
            created_by=current_user.id
        )
        logger.info(
            "Procurement request created: code=%s farm_id=%s input_id=%s by farmer %s",
            procurement_req.request_code,
            procurement_req.farm_id,
            procurement_req.input_id,
            farmer_profile.id
        )
        return ProcurementRequestResponse.model_validate(procurement_req)

    @staticmethod
    def list_farmer_procurements(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> ProcurementListResponse:
        """Retrieves paginated procurement requests for the authenticated farmer."""
        farmer_profile = ProcurementService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size

        items = ProcurementRequestRepository.list_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            status=status_filter,
            farm_id=farm_id,
            search=search
        )
        total = ProcurementRequestRepository.count_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            status=status_filter,
            farm_id=farm_id,
            search=search
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ProcurementListResponse(
            items=[ProcurementRequestResponse.model_validate(p) for p in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_procurement_detail(
        db: Session,
        current_user: User,
        request_id: uuid.UUID
    ) -> ProcurementRequestResponse:
        """Retrieves single procurement request details for the authenticated farmer."""
        farmer_profile = ProcurementService._resolve_farmer_profile(db, current_user)
        procurement_req = ProcurementRequestRepository.get_by_id(
            db=db,
            request_id=request_id,
            farmer_profile_id=farmer_profile.id
        )
        if not procurement_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procurement request not found"
            )
        return ProcurementRequestResponse.model_validate(procurement_req)

    @staticmethod
    def update_procurement(
        db: Session,
        current_user: User,
        request_id: uuid.UUID,
        request: ProcurementRequestUpdate
    ) -> ProcurementRequestResponse:
        """Updates mutable fields of a procurement request if in PENDING status."""
        farmer_profile = ProcurementService._resolve_farmer_profile(db, current_user)
        procurement_req = ProcurementRequestRepository.get_by_id(
            db=db,
            request_id=request_id,
            farmer_profile_id=farmer_profile.id
        )
        if not procurement_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procurement request not found"
            )

        if procurement_req.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit procurement request with status '{procurement_req.status}'. Only PENDING requests may be updated."
            )

        update_dict = request.model_dump(exclude_unset=True)
        if request.preferred_supplier_id:
            supplier = SupplierRepository.get_by_id(db, request.preferred_supplier_id)
            if not supplier or not supplier.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified preferred supplier is inactive or does not exist"
                )

        updated_req = ProcurementRequestRepository.update(
            db=db,
            procurement_req=procurement_req,
            update_data=update_dict,
            updated_by=current_user.id
        )
        logger.info("Procurement request %s updated by user %s", request_id, current_user.id)
        return ProcurementRequestResponse.model_validate(updated_req)

    @staticmethod
    def cancel_procurement(
        db: Session,
        current_user: User,
        request_id: uuid.UUID
    ) -> ProcurementRequestResponse:
        """Cancels a pending procurement request."""
        farmer_profile = ProcurementService._resolve_farmer_profile(db, current_user)
        procurement_req = ProcurementRequestRepository.get_by_id(
            db=db,
            request_id=request_id,
            farmer_profile_id=farmer_profile.id
        )
        if not procurement_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procurement request not found"
            )

        if procurement_req.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel procurement request with status '{procurement_req.status}'. Only PENDING requests can be cancelled."
            )

        updated_req = ProcurementRequestRepository.update_status(
            db=db,
            procurement_req=procurement_req,
            status_value="CANCELLED",
            updated_by=current_user.id
        )
        logger.info("Procurement request %s cancelled by farmer %s", request_id, farmer_profile.id)
        return ProcurementRequestResponse.model_validate(updated_req)

    @staticmethod
    def list_admin_procurements(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        farm_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> ProcurementListResponse:
        """Retrieves paginated procurement requests for Admin."""
        skip = (page - 1) * page_size
        items = ProcurementRequestRepository.list_all(
            db=db,
            skip=skip,
            limit=page_size,
            status=status_filter,
            farm_id=farm_id,
            search=search
        )
        total = ProcurementRequestRepository.count_all(
            db=db,
            status=status_filter,
            farm_id=farm_id,
            search=search
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ProcurementListResponse(
            items=[ProcurementRequestResponse.model_validate(p) for p in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def update_procurement_status_admin(
        db: Session,
        request_id: uuid.UUID,
        request: ProcurementRequestStatusUpdate,
        current_admin: User
    ) -> ProcurementRequestResponse:
        """Admin status update for procurement request."""
        procurement_req = ProcurementRequestRepository.get_by_id(db, request_id=request_id)
        if not procurement_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procurement request not found"
            )

        status_str = request.status.value if hasattr(request.status, "value") else str(request.status)
        updated_req = ProcurementRequestRepository.update_status(
            db=db,
            procurement_req=procurement_req,
            status_value=status_str,
            updated_by=current_admin.id
        )
        logger.info("Procurement request %s status changed to %s by admin %s", request_id, status_str, current_admin.id)
        return ProcurementRequestResponse.model_validate(updated_req)
