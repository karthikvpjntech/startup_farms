import logging
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

from app.models.enums import (
    RoleEnum,
    BillType,
    BillStatus,
    PaymentMethod,
    PaymentStatus,
    LogisticsStatus,
    NotificationType,
    StageStatus,
)
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.models.farm import Farm
from app.models.crop import Crop
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun, CultivationStage, StageExpense
from app.models.worker import Worker
from app.models.machine import Machine
from app.models.worker_attendance import WorkerAttendance
from app.models.machine_usage import MachineUsage
from app.models.material_purchase import MaterialPurchase
from app.models.cultivation_schedule import CultivationSchedule
from app.models.bill import Bill, BillItem
from app.models.payment import Payment
from app.models.logistics import Logistics
from app.models.sms_log import SMSLog
from app.models.supplier import Supplier

from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
from app.repositories.cultivation_repository import CultivationRepository
from app.repositories.farmer_crm_repository import FarmerCRMRepository
from app.services.notification_service import NotificationService

from app.schemas.farmer_crm import (
    WorkerCreate,
    WorkerUpdate,
    WorkerResponse,
    WorkerListResponse,
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    MachineListResponse,
    WorkerAttendanceCreate,
    WorkerAttendanceResponse,
    BulkWorkerAttendanceCreate,
    MachineUsageCreate,
    MachineUsageResponse,
    MaterialPurchaseCreate,
    MaterialPurchaseResponse,
    MaterialPurchaseListResponse,
    CultivationScheduleBulkCreate,
    CultivationScheduleResponse,
    BillCreate,
    BillResponse,
    BillListResponse,
    StageBillGenerateRequest,
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    LogisticsCreate,
    LogisticsStatusUpdate,
    LogisticsResponse,
    LogisticsListResponse,
    SMSSendRequest,
    SMSLogResponse,
    SMSLogListResponse,
    CRMDashboardSummaryResponse,
    CRMTodayActivityItem,
    CRMCultivationDetailResponse,
    CRMTimelineEvent,
    CropCostSummaryResponse,
    StageCostBreakdown,
    CropCostReportItem,
    WorkerPaymentReportItem,
    SupplierPurchaseReportItem,
    FarmExpenseReportItem,
)

logger = logging.getLogger("agri_smart.farmer_crm_service")


class FarmerCRMService:
    """Service orchestrating operations, workflows, billing, payments, and analytics for Farmer CRM."""

    @staticmethod
    def _resolve_farmer_profile(db: Session, current_user: User) -> FarmerProfile:
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.FARMER.value not in user_roles and RoleEnum.SUPER_ADMIN.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the FARMER role",
            )
        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            if RoleEnum.SUPER_ADMIN.value in user_roles:
                profile = FarmerProfileRepository.create(
                    db=db,
                    user_id=current_user.id,
                    profile_data={
                        "address_line1": "Agri-Smart Executive Headquarters",
                        "district": "Central",
                        "state": "Maharashtra",
                        "pincode": "422001",
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Farmer profile must be registered before managing farm operations",
                )
        return profile

    # ==========================================
    # Worker Master Service
    # ==========================================

    @staticmethod
    def create_worker(
        db: Session,
        current_user: User,
        request: WorkerCreate,
    ) -> WorkerResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)

        # Check if worker already exists with same mobile number for this farmer
        existing = FarmerCRMRepository.get_worker_by_mobile(
            db=db,
            farmer_profile_id=farmer_profile.id,
            mobile_number=request.mobile_number,
        )
        if existing:
            # Reusable worker already in database
            logger.info("Reusing existing worker %s for mobile %s", existing.id, request.mobile_number)
            return WorkerResponse.model_validate(existing)

        worker = FarmerCRMRepository.create_worker(
            db=db,
            farmer_profile_id=farmer_profile.id,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        logger.info("New worker %s (%s) registered into Worker Master", worker.worker_code, worker.full_name)
        return WorkerResponse.model_validate(worker)

    @staticmethod
    def list_workers(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        skill: Optional[str] = None,
        gender: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> WorkerListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        items = FarmerCRMRepository.list_workers(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            search=search,
            skill=skill,
            gender=gender,
            is_active=is_active,
        )
        total = FarmerCRMRepository.count_workers(
            db=db,
            farmer_profile_id=farmer_profile.id,
            search=search,
            skill=skill,
            gender=gender,
            is_active=is_active,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return WorkerListResponse(
            items=[WorkerResponse.model_validate(w) for w in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    def get_worker(
        db: Session,
        current_user: User,
        worker_id: uuid.UUID,
    ) -> WorkerResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        worker = FarmerCRMRepository.get_worker_by_id(db, worker_id, farmer_profile.id)
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
        return WorkerResponse.model_validate(worker)

    @staticmethod
    def update_worker(
        db: Session,
        current_user: User,
        worker_id: uuid.UUID,
        request: WorkerUpdate,
    ) -> WorkerResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        worker = FarmerCRMRepository.get_worker_by_id(db, worker_id, farmer_profile.id)
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
        updated = FarmerCRMRepository.update_worker(
            db=db,
            worker=worker,
            data=request.model_dump(exclude_unset=True),
            updated_by=current_user.id,
        )
        return WorkerResponse.model_validate(updated)

    @staticmethod
    def delete_worker(
        db: Session,
        current_user: User,
        worker_id: uuid.UUID,
    ) -> WorkerResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        worker = FarmerCRMRepository.get_worker_by_id(db, worker_id, farmer_profile.id)
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
        deleted = FarmerCRMRepository.soft_delete_worker(db, worker, deleted_by=current_user.id)
        return WorkerResponse.model_validate(deleted)

    # ==========================================
    # Machine Master Service
    # ==========================================

    @staticmethod
    def create_machine(
        db: Session,
        current_user: User,
        request: MachineCreate,
    ) -> MachineResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        machine = FarmerCRMRepository.create_machine(
            db=db,
            farmer_profile_id=farmer_profile.id,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        logger.info("Machine %s registered: %s", machine.machine_code, machine.machine_name)
        return MachineResponse.model_validate(machine)

    @staticmethod
    def list_machines(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        machine_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> MachineListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        items = FarmerCRMRepository.list_machines(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            search=search,
            machine_type=machine_type,
            is_active=is_active,
        )
        total = FarmerCRMRepository.count_machines(
            db=db,
            farmer_profile_id=farmer_profile.id,
            search=search,
            machine_type=machine_type,
            is_active=is_active,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return MachineListResponse(
            items=[MachineResponse.model_validate(m) for m in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    def update_machine(
        db: Session,
        current_user: User,
        machine_id: uuid.UUID,
        request: MachineUpdate,
    ) -> MachineResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        machine = FarmerCRMRepository.get_machine_by_id(db, machine_id, farmer_profile.id)
        if not machine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
        updated = FarmerCRMRepository.update_machine(
            db=db,
            machine=machine,
            data=request.model_dump(exclude_unset=True),
            updated_by=current_user.id,
        )
        return MachineResponse.model_validate(updated)

    @staticmethod
    def delete_machine(
        db: Session,
        current_user: User,
        machine_id: uuid.UUID,
    ) -> MachineResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        machine = FarmerCRMRepository.get_machine_by_id(db, machine_id, farmer_profile.id)
        if not machine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
        deleted = FarmerCRMRepository.soft_delete_machine(db, machine, deleted_by=current_user.id)
        return MachineResponse.model_validate(deleted)

    # ==========================================
    # Worker Attendance Service
    # ==========================================

    @staticmethod
    def add_worker_attendance(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: WorkerAttendanceCreate,
    ) -> WorkerAttendanceResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

        worker = FarmerCRMRepository.get_worker_by_id(db, request.worker_id, farmer_profile.id)
        if not worker or not worker.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active worker not found in Worker Master")

        att = FarmerCRMRepository.add_attendance(
            db=db,
            stage=stage,
            worker=worker,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        return WorkerAttendanceResponse(
            id=att.id,
            stage_id=att.stage_id,
            cultivation_id=att.cultivation_id,
            worker_id=att.worker_id,
            worker_name=worker.full_name,
            worker_code=worker.worker_code,
            gender=worker.gender,
            skill=worker.skill,
            mobile_number=worker.mobile_number,
            work_date=att.work_date,
            start_time=att.start_time,
            end_time=att.end_time,
            break_hours=att.break_hours,
            total_hours=att.total_hours,
            working_days=att.working_days,
            daily_salary=att.daily_salary,
            overtime_amount=att.overtime_amount,
            calculated_amount=att.calculated_amount,
            payment_status=att.payment_status,
            bill_id=att.bill_id,
            notes=att.notes,
            created_at=att.created_at,
        )

    @staticmethod
    def bulk_add_worker_attendance(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: BulkWorkerAttendanceCreate,
    ) -> List[WorkerAttendanceResponse]:
        results = []
        for att_req in request.attendances:
            res = FarmerCRMService.add_worker_attendance(db, current_user, stage_id, att_req)
            results.append(res)
        return results

    @staticmethod
    def list_stage_attendances(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> List[WorkerAttendanceResponse]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

        attendances = FarmerCRMRepository.list_attendances_by_stage(db, stage_id)
        return [
            WorkerAttendanceResponse(
                id=a.id,
                stage_id=a.stage_id,
                cultivation_id=a.cultivation_id,
                worker_id=a.worker_id,
                worker_name=a.worker.full_name if a.worker else "Unknown",
                worker_code=a.worker.worker_code if a.worker else "WKR-000",
                gender=a.worker.gender if a.worker else "MALE",
                skill=a.worker.skill if a.worker else "GENERAL_LABOR",
                mobile_number=a.worker.mobile_number if a.worker else "",
                work_date=a.work_date,
                start_time=a.start_time,
                end_time=a.end_time,
                break_hours=a.break_hours,
                total_hours=a.total_hours,
                working_days=a.working_days,
                daily_salary=a.daily_salary,
                overtime_amount=a.overtime_amount,
                calculated_amount=a.calculated_amount,
                payment_status=a.payment_status,
                bill_id=a.bill_id,
                notes=a.notes,
                created_at=a.created_at,
            )
            for a in attendances
        ]

    @staticmethod
    def delete_attendance(
        db: Session,
        current_user: User,
        attendance_id: uuid.UUID,
    ) -> WorkerAttendanceResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        att = FarmerCRMRepository.get_attendance_by_id(db, attendance_id)
        if not att or att.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker attendance record not found")

        deleted = FarmerCRMRepository.soft_delete_attendance(db, att, deleted_by=current_user.id)
        return WorkerAttendanceResponse(
            id=deleted.id,
            stage_id=deleted.stage_id,
            cultivation_id=deleted.cultivation_id,
            worker_id=deleted.worker_id,
            worker_name=deleted.worker.full_name if deleted.worker else "Unknown",
            worker_code=deleted.worker.worker_code if deleted.worker else "WKR-000",
            gender=deleted.worker.gender if deleted.worker else "MALE",
            skill=deleted.worker.skill if deleted.worker else "GENERAL_LABOR",
            mobile_number=deleted.worker.mobile_number if deleted.worker else "",
            work_date=deleted.work_date,
            start_time=deleted.start_time,
            end_time=deleted.end_time,
            break_hours=deleted.break_hours,
            total_hours=deleted.total_hours,
            working_days=deleted.working_days,
            daily_salary=deleted.daily_salary,
            overtime_amount=deleted.overtime_amount,
            calculated_amount=deleted.calculated_amount,
            payment_status=deleted.payment_status,
            bill_id=deleted.bill_id,
            notes=deleted.notes,
            created_at=deleted.created_at,
        )

    # ==========================================
    # Machine Usage Service
    # ==========================================

    @staticmethod
    def add_machine_usage(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: MachineUsageCreate,
    ) -> MachineUsageResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

        machine = FarmerCRMRepository.get_machine_by_id(db, request.machine_id, farmer_profile.id)
        if not machine or not machine.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active machine not found in Machine Master")

        usage = FarmerCRMRepository.add_machine_usage(
            db=db,
            stage=stage,
            machine=machine,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        return MachineUsageResponse(
            id=usage.id,
            stage_id=usage.stage_id,
            cultivation_id=usage.cultivation_id,
            machine_id=usage.machine_id,
            machine_name=machine.machine_name,
            machine_code=machine.machine_code,
            machine_type=machine.machine_type,
            usage_date=usage.usage_date,
            hours_used=usage.hours_used,
            days_used=usage.days_used,
            rate_applied=usage.rate_applied,
            fuel_cost=usage.fuel_cost,
            operator_cost=usage.operator_cost,
            total_cost=usage.total_cost,
            bill_id=usage.bill_id,
            notes=usage.notes,
            created_at=usage.created_at,
        )

    @staticmethod
    def list_stage_machine_usages(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> List[MachineUsageResponse]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

        usages = FarmerCRMRepository.list_machine_usages_by_stage(db, stage_id)
        return [
            MachineUsageResponse(
                id=u.id,
                stage_id=u.stage_id,
                cultivation_id=u.cultivation_id,
                machine_id=u.machine_id,
                machine_name=u.machine.machine_name if u.machine else "Unknown Machine",
                machine_code=u.machine.machine_code if u.machine else "MCH-000",
                machine_type=u.machine.machine_type if u.machine else "TRACTOR",
                usage_date=u.usage_date,
                hours_used=u.hours_used,
                days_used=u.days_used,
                rate_applied=u.rate_applied,
                fuel_cost=u.fuel_cost,
                operator_cost=u.operator_cost,
                total_cost=u.total_cost,
                bill_id=u.bill_id,
                notes=u.notes,
                created_at=u.created_at,
            )
            for u in usages
        ]

    @staticmethod
    def delete_machine_usage(
        db: Session,
        current_user: User,
        usage_id: uuid.UUID,
    ) -> MachineUsageResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        usage = FarmerCRMRepository.get_machine_usage_by_id(db, usage_id)
        if not usage or usage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine usage not found")

        deleted = FarmerCRMRepository.soft_delete_machine_usage(db, usage, deleted_by=current_user.id)
        return MachineUsageResponse(
            id=deleted.id,
            stage_id=deleted.stage_id,
            cultivation_id=deleted.cultivation_id,
            machine_id=deleted.machine_id,
            machine_name=deleted.machine.machine_name if deleted.machine else "Unknown",
            machine_code=deleted.machine.machine_code if deleted.machine else "MCH-000",
            machine_type=deleted.machine.machine_type if deleted.machine else "TRACTOR",
            usage_date=deleted.usage_date,
            hours_used=deleted.hours_used,
            days_used=deleted.days_used,
            rate_applied=deleted.rate_applied,
            fuel_cost=deleted.fuel_cost,
            operator_cost=deleted.operator_cost,
            total_cost=deleted.total_cost,
            bill_id=deleted.bill_id,
            notes=deleted.notes,
            created_at=deleted.created_at,
        )

    # ==========================================
    # Material Purchases Service
    # ==========================================

    @staticmethod
    def create_material_purchase(
        db: Session,
        current_user: User,
        request: MaterialPurchaseCreate,
    ) -> MaterialPurchaseResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        supplier = db.scalar(
            select(Supplier).where(Supplier.id == request.supplier_id, Supplier.is_deleted == False)
        )
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

        purchase = FarmerCRMRepository.create_material_purchase(
            db=db,
            farmer_profile_id=farmer_profile.id,
            supplier=supplier,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        return MaterialPurchaseResponse(
            id=purchase.id,
            purchase_code=purchase.purchase_code,
            farmer_profile_id=purchase.farmer_profile_id,
            cultivation_id=purchase.cultivation_id,
            stage_id=purchase.stage_id,
            supplier_id=purchase.supplier_id,
            supplier_name=supplier.supplier_name,
            supplier_contact=supplier.phone_number,
            material_category=purchase.material_category,
            material_name=purchase.material_name,
            quantity=purchase.quantity,
            unit=purchase.unit,
            unit_rate=purchase.unit_rate,
            subtotal=purchase.subtotal,
            tax_amount=purchase.tax_amount,
            total_amount=purchase.total_amount,
            purchase_date=purchase.purchase_date,
            payment_status=purchase.payment_status,
            bill_id=purchase.bill_id,
            notes=purchase.notes,
            created_at=purchase.created_at,
        )

    @staticmethod
    def list_purchases(
        db: Session,
        current_user: User,
        cultivation_id: Optional[uuid.UUID] = None,
        stage_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> MaterialPurchaseListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        purchases = FarmerCRMRepository.list_purchases(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
            stage_id=stage_id,
            skip=skip,
            limit=page_size,
        )
        total = FarmerCRMRepository.count_purchases(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        items = [
            MaterialPurchaseResponse(
                id=p.id,
                purchase_code=p.purchase_code,
                farmer_profile_id=p.farmer_profile_id,
                cultivation_id=p.cultivation_id,
                stage_id=p.stage_id,
                supplier_id=p.supplier_id,
                supplier_name=p.supplier.supplier_name if p.supplier else "Unknown Supplier",
                supplier_contact=p.supplier.phone_number if p.supplier else "",
                material_category=p.material_category,
                material_name=p.material_name,
                quantity=p.quantity,
                unit=p.unit,
                unit_rate=p.unit_rate,
                subtotal=p.subtotal,
                tax_amount=p.tax_amount,
                total_amount=p.total_amount,
                purchase_date=p.purchase_date,
                payment_status=p.payment_status,
                bill_id=p.bill_id,
                notes=p.notes,
                created_at=p.created_at,
            )
            for p in purchases
        ]
        return MaterialPurchaseListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    # ==========================================
    # Cultivation Schedules Service
    # ==========================================

    @staticmethod
    def create_or_update_schedules(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
        request: CultivationScheduleBulkCreate,
    ) -> List[CultivationScheduleResponse]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(db, cultivation_id, farmer_profile.id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation run not found")

        schedules = FarmerCRMRepository.create_or_update_schedules(
            db=db,
            cultivation_id=cultivation_id,
            schedules_data=[s.model_dump() for s in request.schedules],
            created_by=current_user.id,
        )
        return [CultivationScheduleResponse.model_validate(s) for s in schedules]

    @staticmethod
    def get_schedules(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> List[CultivationScheduleResponse]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(db, cultivation_id, farmer_profile.id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation run not found")
        schedules = FarmerCRMRepository.get_schedules(db, cultivation_id)
        return [CultivationScheduleResponse.model_validate(s) for s in schedules]

    # ==========================================
    # Billing Service
    # ==========================================

    @staticmethod
    def _format_bill_response(bill: Bill) -> BillResponse:
        farm = bill.farm
        crop_name = bill.cultivation.farm_crop_plan.crop.crop_name if bill.cultivation and bill.cultivation.farm_crop_plan and bill.cultivation.farm_crop_plan.crop else None
        stage_name = bill.stage.stage_name if bill.stage else None

        return BillResponse(
            id=bill.id,
            bill_number=bill.bill_number,
            farmer_profile_id=bill.farmer_profile_id,
            farm_id=bill.farm_id,
            farm_name=farm.farm_name if farm else "Unknown Farm",
            cultivation_id=bill.cultivation_id,
            crop_name=crop_name,
            stage_id=bill.stage_id,
            stage_name=stage_name,
            bill_type=bill.bill_type,
            recipient_name=bill.recipient_name,
            recipient_type=bill.recipient_type,
            recipient_worker_id=bill.recipient_worker_id,
            recipient_supplier_id=bill.recipient_supplier_id,
            bill_date=bill.bill_date,
            due_date=bill.due_date,
            subtotal=bill.subtotal,
            tax_amount=bill.tax_amount,
            discount_amount=bill.discount_amount,
            total_amount=bill.total_amount,
            paid_amount=bill.paid_amount,
            pending_amount=bill.pending_amount,
            status=bill.status,
            notes=bill.notes,
            items=[
                {
                    "id": itm.id,
                    "bill_id": itm.bill_id,
                    "item_type": itm.item_type,
                    "item_description": itm.item_description,
                    "quantity": itm.quantity,
                    "unit": itm.unit,
                    "unit_price": itm.unit_price,
                    "total_price": itm.total_price,
                }
                for itm in bill.items
            ],
            created_at=bill.created_at,
            updated_at=bill.updated_at,
        )

    @staticmethod
    def generate_stage_bill(
        db: Session,
        current_user: User,
        request: StageBillGenerateRequest,
    ) -> BillResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, request.stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

        run = stage.cultivation
        farm = run.farm_crop_plan.farm if run.farm_crop_plan else None
        if not farm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Farm not associated with cultivation")

        items_data = []

        # 1. Collect Unbilled Worker Attendance
        if request.include_workers:
            attendances = db.scalars(
                select(WorkerAttendance).where(
                    and_(
                        WorkerAttendance.stage_id == stage.id,
                        WorkerAttendance.bill_id == None,
                        WorkerAttendance.is_deleted == False,
                    )
                )
            ).all()
            for att in attendances:
                worker_name = att.worker.full_name if att.worker else "Worker"
                items_data.append(
                    {
                        "item_type": "LABOR",
                        "item_description": f"Labor Wages - {worker_name} ({att.working_days} days @ ₹{att.daily_salary}/day)",
                        "quantity": att.working_days,
                        "unit": "DAYS",
                        "unit_price": att.daily_salary,
                        "total_price": att.calculated_amount,
                    }
                )

        # 2. Collect Unbilled Machine Usages
        if request.include_machines:
            usages = db.scalars(
                select(MachineUsage).where(
                    and_(
                        MachineUsage.stage_id == stage.id,
                        MachineUsage.bill_id == None,
                        MachineUsage.is_deleted == False,
                    )
                )
            ).all()
            for u in usages:
                machine_name = u.machine.machine_name if u.machine else "Machine"
                qty = u.hours_used if u.hours_used > 0 else u.days_used
                unit_str = "HRS" if u.hours_used > 0 else "DAYS"
                items_data.append(
                    {
                        "item_type": "MACHINE",
                        "item_description": f"Machinery Cost - {machine_name} ({qty} {unit_str})",
                        "quantity": qty if qty > 0 else Decimal("1.00"),
                        "unit": unit_str,
                        "unit_price": u.rate_applied,
                        "total_price": u.total_cost,
                    }
                )

        # 3. Collect Unbilled Stage Expenses (e.g. other fuel, refreshments, inputs)
        if request.include_other:
            expenses = db.scalars(
                select(StageExpense).where(
                    and_(
                        StageExpense.stage_id == stage.id,
                        StageExpense.is_deleted == False,
                    )
                )
            ).all()
            for exp in expenses:
                items_data.append(
                    {
                        "item_type": exp.expense_category,
                        "item_description": exp.title,
                        "quantity": Decimal("1.00"),
                        "unit": "UNIT",
                        "unit_price": exp.amount,
                        "total_price": exp.amount,
                    }
                )

        if not items_data:
            # Fallback single stage item if no logs yet
            items_data.append(
                {
                    "item_type": "LABOR",
                    "item_description": f"Cultivation Stage Work - {stage.stage_name}",
                    "quantity": Decimal("1.00"),
                    "unit": "STAGE",
                    "unit_price": Decimal("0.00"),
                    "total_price": Decimal("0.00"),
                }
            )

        bill = FarmerCRMRepository.create_bill(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_id=farm.id,
            bill_type=BillType.STAGE_CONSOLIDATED.value,
            recipient_name=f"Farm Stage Bill - {stage.stage_name}",
            recipient_type="CONSOLIDATED",
            items_data=items_data,
            cultivation_id=run.id,
            stage_id=stage.id,
            notes=request.notes or f"Generated bill for completed stage {stage.stage_name}",
            created_by=current_user.id,
        )

        # Link attendances and usages to this bill
        if request.include_workers:
            for att in db.scalars(select(WorkerAttendance).where(WorkerAttendance.stage_id == stage.id)).all():
                if not att.bill_id:
                    att.bill_id = bill.id
        if request.include_machines:
            for u in db.scalars(select(MachineUsage).where(MachineUsage.stage_id == stage.id)).all():
                if not u.bill_id:
                    u.bill_id = bill.id
        db.commit()
        db.refresh(bill)

        logger.info("Generated Stage Bill %s for Stage %s (Total: ₹%s)", bill.bill_number, stage.id, bill.total_amount)
        return FarmerCRMService._format_bill_response(bill)

    @staticmethod
    def create_custom_bill(
        db: Session,
        current_user: User,
        request: BillCreate,
    ) -> BillResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(db, request.farm_id, farmer_profile.id)
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        bill = FarmerCRMRepository.create_bill(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_id=farm.id,
            bill_type=request.bill_type.value if hasattr(request.bill_type, "value") else str(request.bill_type),
            recipient_name=request.recipient_name,
            recipient_type=request.recipient_type,
            items_data=[itm.model_dump() for itm in request.items],
            cultivation_id=request.cultivation_id,
            stage_id=request.stage_id,
            recipient_worker_id=request.recipient_worker_id,
            recipient_supplier_id=request.recipient_supplier_id,
            bill_date=request.bill_date,
            due_date=request.due_date,
            tax_amount=request.tax_amount,
            discount_amount=request.discount_amount,
            notes=request.notes,
            created_by=current_user.id,
        )
        return FarmerCRMService._format_bill_response(bill)

    @staticmethod
    def get_bill(
        db: Session,
        current_user: User,
        bill_id: uuid.UUID,
    ) -> BillResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        bill = FarmerCRMRepository.get_bill_by_id(db, bill_id, farmer_profile.id)
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
        return FarmerCRMService._format_bill_response(bill)

    @staticmethod
    def list_bills(
        db: Session,
        current_user: User,
        cultivation_id: Optional[uuid.UUID] = None,
        stage_id: Optional[uuid.UUID] = None,
        status_val: Optional[str] = None,
        bill_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> BillListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        bills = FarmerCRMRepository.list_bills(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
            stage_id=stage_id,
            status=status_val,
            bill_type=bill_type,
            skip=skip,
            limit=page_size,
        )
        total = FarmerCRMRepository.count_bills(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
            status=status_val,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return BillListResponse(
            items=[FarmerCRMService._format_bill_response(b) for b in bills],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    # ==========================================
    # Payments Checkout Service
    # ==========================================

    @staticmethod
    def record_payment(
        db: Session,
        current_user: User,
        request: PaymentCreate,
    ) -> PaymentResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        bill = FarmerCRMRepository.get_bill_by_id(db, request.bill_id, farmer_profile.id)
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")

        # Payment amount safety validation
        if bill.status == BillStatus.PAID.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This bill is already fully settled")
        if request.amount > bill.pending_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount ₹{request.amount} exceeds pending bill balance of ₹{bill.pending_amount}",
            )

        payment_method_str = request.payment_method.value if hasattr(request.payment_method, "value") else str(request.payment_method)

        payment = FarmerCRMRepository.create_payment(
            db=db,
            bill=bill,
            amount=request.amount,
            payment_method=payment_method_str,
            transaction_reference=request.transaction_reference,
            payment_date=request.payment_date,
            notes=request.notes,
            created_by=current_user.id,
        )

        # Trigger SMS Notification if enabled
        if request.send_sms_notification:
            farm_name = bill.farm.farm_name if bill.farm else "Farm"
            stage_title = bill.stage.stage_name if bill.stage else "Cultivation Work"

            # Check if there are individual worker attendances linked to this bill
            attendances = db.scalars(
                select(WorkerAttendance).where(WorkerAttendance.bill_id == bill.id)
            ).all()

            if attendances:
                for att in attendances:
                    if att.worker and att.worker.mobile_number:
                        sms_msg = (
                            f"Dear {att.worker.full_name},\n\n"
                            f"Your work for {stage_title} at {farm_name}\n"
                            f"has been completed.\n\n"
                            f"Working Days: {att.working_days}\n"
                            f"Amount: ₹{att.calculated_amount}\n"
                            f"Payment Status: PAID\n\n"
                            f"Thank you."
                        )
                        NotificationService.send_sms(
                            db=db,
                            farmer_profile_id=farmer_profile.id,
                            recipient_mobile=att.worker.mobile_number,
                            recipient_name=att.worker.full_name,
                            message_body=sms_msg,
                            recipient_type="WORKER",
                            notification_type=NotificationType.WORK_COMPLETED_PAYMENT.value,
                            related_entity_type="WORKER_ATTENDANCE",
                            related_entity_id=att.id,
                        )
            else:
                recipient_mobile = ""
                recipient_name = bill.recipient_name
                recipient_type = bill.recipient_type

                if bill.recipient_worker_id and bill.worker:
                    recipient_mobile = bill.worker.mobile_number
                    recipient_name = bill.worker.full_name
                elif bill.recipient_supplier_id and bill.supplier:
                    recipient_mobile = bill.supplier.phone_number
                    recipient_name = bill.supplier.supplier_name

                if recipient_mobile:
                    sms_msg = (
                        f"Dear {recipient_name},\n\n"
                        f"Your payment for {stage_title} at {farm_name}\n"
                        f"has been processed.\n\n"
                        f"Amount: ₹{payment.amount} | Method: {payment.payment_method}\n"
                        f"Payment Status: PAID (Ref: {payment.payment_number})\n\n"
                        f"Thank you."
                    )
                    NotificationService.send_sms(
                        db=db,
                        farmer_profile_id=farmer_profile.id,
                        recipient_mobile=recipient_mobile,
                        recipient_name=recipient_name,
                        message_body=sms_msg,
                        recipient_type=recipient_type,
                        notification_type=NotificationType.PAYMENT_RECEIPT.value,
                        related_entity_type="PAYMENT",
                        related_entity_id=payment.id,
                    )


        logger.info("Payment %s (₹%s) processed for Bill %s", payment.payment_number, payment.amount, bill.bill_number)
        return PaymentResponse(
            id=payment.id,
            payment_number=payment.payment_number,
            bill_id=payment.bill_id,
            bill_number=bill.bill_number,
            farmer_profile_id=payment.farmer_profile_id,
            amount=payment.amount,
            payment_method=payment.payment_method,
            payment_date=payment.payment_date,
            status=payment.status,
            transaction_reference=payment.transaction_reference,
            recipient_name=bill.recipient_name,
            notes=payment.notes,
            created_at=payment.created_at,
        )

    @staticmethod
    def list_payments(
        db: Session,
        current_user: User,
        bill_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaymentListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        payments = FarmerCRMRepository.list_payments(
            db=db,
            farmer_profile_id=farmer_profile.id,
            bill_id=bill_id,
            skip=skip,
            limit=page_size,
        )
        total = FarmerCRMRepository.count_payments(
            db=db,
            farmer_profile_id=farmer_profile.id,
            bill_id=bill_id,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        items = [
            PaymentResponse(
                id=p.id,
                payment_number=p.payment_number,
                bill_id=p.bill_id,
                bill_number=p.bill.bill_number if p.bill else "BILL-000",
                farmer_profile_id=p.farmer_profile_id,
                amount=p.amount,
                payment_method=p.payment_method,
                payment_date=p.payment_date,
                status=p.status,
                transaction_reference=p.transaction_reference,
                recipient_name=p.bill.recipient_name if p.bill else "Recipient",
                notes=p.notes,
                created_at=p.created_at,
            )
            for p in payments
        ]
        return PaymentListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    # ==========================================
    # Logistics Service
    # ==========================================

    @staticmethod
    def create_logistics(
        db: Session,
        current_user: User,
        request: LogisticsCreate,
    ) -> LogisticsResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(db, request.cultivation_id, farmer_profile.id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation run not found")

        farm = FarmRepository.get_by_id(db, request.farm_id, farmer_profile.id)
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        logistics = FarmerCRMRepository.create_logistics(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=run.id,
            farm_id=farm.id,
            data=request.model_dump(),
            created_by=current_user.id,
        )
        crop_name = run.farm_crop_plan.crop.crop_name if run.farm_crop_plan and run.farm_crop_plan.crop else "Harvest"
        return LogisticsResponse(
            id=logistics.id,
            dispatch_code=logistics.dispatch_code,
            farmer_profile_id=logistics.farmer_profile_id,
            cultivation_id=logistics.cultivation_id,
            crop_name=crop_name,
            farm_id=logistics.farm_id,
            farm_name=farm.farm_name,
            harvest_location=logistics.harvest_location,
            destination=logistics.destination,
            pickup_date=logistics.pickup_date,
            delivery_date=logistics.delivery_date,
            vehicle_number=logistics.vehicle_number,
            driver_name=logistics.driver_name,
            driver_contact=logistics.driver_contact,
            driver_id=logistics.driver_id,
            quantity_transported=logistics.quantity_transported,
            quantity_unit=logistics.quantity_unit,
            transport_cost=logistics.transport_cost,
            loading_cost=logistics.loading_cost,
            unloading_cost=logistics.unloading_cost,
            total_logistics_cost=logistics.total_logistics_cost,
            status=logistics.status,
            bill_id=logistics.bill_id,
            notes=logistics.notes,
            created_at=logistics.created_at,
        )

    @staticmethod
    def list_logistics(
        db: Session,
        current_user: User,
        cultivation_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> LogisticsListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        items = FarmerCRMRepository.list_logistics(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
            skip=skip,
            limit=page_size,
        )
        total = FarmerCRMRepository.count_logistics(
            db=db,
            farmer_profile_id=farmer_profile.id,
            cultivation_id=cultivation_id,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        res_items = []
        for l in items:
            crop_name = l.cultivation.farm_crop_plan.crop.crop_name if l.cultivation and l.cultivation.farm_crop_plan and l.cultivation.farm_crop_plan.crop else "Harvest"
            farm_name = l.farm.farm_name if l.farm else "Farm"
            res_items.append(
                LogisticsResponse(
                    id=l.id,
                    dispatch_code=l.dispatch_code,
                    farmer_profile_id=l.farmer_profile_id,
                    cultivation_id=l.cultivation_id,
                    crop_name=crop_name,
                    farm_id=l.farm_id,
                    farm_name=farm_name,
                    harvest_location=l.harvest_location,
                    destination=l.destination,
                    pickup_date=l.pickup_date,
                    delivery_date=l.delivery_date,
                    vehicle_number=l.vehicle_number,
                    driver_name=l.driver_name,
                    driver_contact=l.driver_contact,
                    driver_id=l.driver_id,
                    quantity_transported=l.quantity_transported,
                    quantity_unit=l.quantity_unit,
                    transport_cost=l.transport_cost,
                    loading_cost=l.loading_cost,
                    unloading_cost=l.unloading_cost,
                    total_logistics_cost=l.total_logistics_cost,
                    status=l.status,
                    bill_id=l.bill_id,
                    notes=l.notes,
                    created_at=l.created_at,
                )
            )
        return LogisticsListResponse(
            items=res_items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    def update_logistics_status(
        db: Session,
        current_user: User,
        logistics_id: uuid.UUID,
        request: LogisticsStatusUpdate,
    ) -> LogisticsResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        logistics = FarmerCRMRepository.get_logistics_by_id(db, logistics_id)
        if not logistics or logistics.farmer_profile_id != farmer_profile.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logistics dispatch not found")

        status_str = request.status.value if hasattr(request.status, "value") else str(request.status)
        updated = FarmerCRMRepository.update_logistics_status(
            db=db,
            logistics=logistics,
            status_val=status_str,
            delivery_date=request.delivery_date,
            notes=request.notes,
            updated_by=current_user.id,
        )
        crop_name = updated.cultivation.farm_crop_plan.crop.crop_name if updated.cultivation and updated.cultivation.farm_crop_plan and updated.cultivation.farm_crop_plan.crop else "Harvest"
        return LogisticsResponse(
            id=updated.id,
            dispatch_code=updated.dispatch_code,
            farmer_profile_id=updated.farmer_profile_id,
            cultivation_id=updated.cultivation_id,
            crop_name=crop_name,
            farm_id=updated.farm_id,
            farm_name=updated.farm.farm_name if updated.farm else "Farm",
            harvest_location=updated.harvest_location,
            destination=updated.destination,
            pickup_date=updated.pickup_date,
            delivery_date=updated.delivery_date,
            vehicle_number=updated.vehicle_number,
            driver_name=updated.driver_name,
            driver_contact=updated.driver_contact,
            driver_id=updated.driver_id,
            quantity_transported=updated.quantity_transported,
            quantity_unit=updated.quantity_unit,
            transport_cost=updated.transport_cost,
            loading_cost=updated.loading_cost,
            unloading_cost=updated.unloading_cost,
            total_logistics_cost=updated.total_logistics_cost,
            status=updated.status,
            bill_id=updated.bill_id,
            notes=updated.notes,
            created_at=updated.created_at,
        )

    # ==========================================
    # SMS & Notification Service
    # ==========================================

    @staticmethod
    def send_manual_sms(
        db: Session,
        current_user: User,
        request: SMSSendRequest,
    ) -> SMSLogResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        log = NotificationService.send_sms(
            db=db,
            farmer_profile_id=farmer_profile.id,
            recipient_mobile=request.recipient_mobile,
            recipient_name=request.recipient_name,
            message_body=request.message_body,
            recipient_type=request.recipient_type,
            notification_type=request.notification_type.value if hasattr(request.notification_type, "value") else str(request.notification_type),
            related_entity_type=request.related_entity_type,
            related_entity_id=request.related_entity_id,
        )
        return SMSLogResponse.model_validate(log)

    @staticmethod
    def list_sms_logs(
        db: Session,
        current_user: User,
        cursor: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> SMSLogListResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        total = FarmerCRMRepository.count_sms_logs(db, farmer_profile.id)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Keyset / Cursor Pagination Mode
        if cursor:
            cursor_time = None
            cursor_id = None
            try:
                parts = cursor.split("_", 1)
                cursor_time = datetime.fromisoformat(parts[0])
                if len(parts) > 1:
                    cursor_id = uuid.UUID(parts[1])
            except Exception:
                pass

            raw_logs = FarmerCRMRepository.list_sms_logs_cursor(
                db=db,
                farmer_profile_id=farmer_profile.id,
                cursor_created_at=cursor_time,
                cursor_id=cursor_id,
                limit=page_size,
            )
            has_more = len(raw_logs) > page_size
            logs = raw_logs[:page_size]
            next_cursor = None
            if has_more and logs:
                last_log = logs[-1]
                next_cursor = f"{last_log.created_at.isoformat()}_{last_log.id}"

            return SMSLogListResponse(
                items=[SMSLogResponse.model_validate(l) for l in logs],
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
                next_cursor=next_cursor,
                has_more=has_more,
            )

        # Standard Numbered Offset Mode
        skip = (page - 1) * page_size
        logs = FarmerCRMRepository.list_sms_logs(db, farmer_profile.id, skip=skip, limit=page_size)
        has_more = (skip + len(logs)) < total
        next_cursor = None
        if logs and has_more:
            last_log = logs[-1]
            next_cursor = f"{last_log.created_at.isoformat()}_{last_log.id}"

        return SMSLogListResponse(
            items=[SMSLogResponse.model_validate(l) for l in logs],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    # ==========================================
    # CRM Dashboard Summary Analytics
    # ==========================================

    @staticmethod
    def get_dashboard_summary(
        db: Session,
        current_user: User,
    ) -> CRMDashboardSummaryResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        fid = farmer_profile.id

        # 1. Total Farms
        total_farms = db.scalar(
            select(func.count(Farm.id)).where(Farm.farmer_profile_id == fid, Farm.is_deleted == False)
        ) or 0

        # 2. Active Crop Plans
        active_crop_plans = db.scalar(
            select(func.count(FarmCropPlan.id))
            .join(Farm, FarmCropPlan.farm_id == Farm.id)
            .where(Farm.farmer_profile_id == fid, FarmCropPlan.is_active == True, FarmCropPlan.is_deleted == False)
        ) or 0

        # 3. Active Cultivations
        active_cultivations = db.scalar(
            select(func.count(CultivationRun.id)).where(
                CultivationRun.farmer_profile_id == fid,
                CultivationRun.is_active == True,
                CultivationRun.is_deleted == False,
            )
        ) or 0

        # 4. Total Workers & Machines currently assigned
        workers_assigned = db.scalar(
            select(func.count(func.distinct(WorkerAttendance.worker_id)))
            .join(CultivationRun, WorkerAttendance.cultivation_id == CultivationRun.id)
            .where(
                CultivationRun.farmer_profile_id == fid,
                CultivationRun.is_active == True,
                WorkerAttendance.is_deleted == False,
            )
        ) or 0

        machines_assigned = db.scalar(
            select(func.count(func.distinct(MachineUsage.machine_id)))
            .join(CultivationRun, MachineUsage.cultivation_id == CultivationRun.id)
            .where(
                CultivationRun.farmer_profile_id == fid,
                CultivationRun.is_active == True,
                MachineUsage.is_deleted == False,
            )
        ) or 0

        # 5. Purchases Count
        purchases_count = db.scalar(
            select(func.count(MaterialPurchase.id)).where(
                MaterialPurchase.farmer_profile_id == fid,
                MaterialPurchase.is_deleted == False,
            )
        ) or 0

        # 6. Total Costs, Pending Payments, and Completed Payments
        total_bills_amount = db.scalar(
            select(func.sum(Bill.total_amount)).where(Bill.farmer_profile_id == fid, Bill.is_deleted == False)
        ) or Decimal("0.00")

        pending_payments = db.scalar(
            select(func.sum(Bill.pending_amount)).where(Bill.farmer_profile_id == fid, Bill.is_deleted == False)
        ) or Decimal("0.00")

        completed_payments = db.scalar(
            select(func.sum(Payment.amount)).where(Payment.farmer_profile_id == fid, Payment.is_deleted == False)
        ) or Decimal("0.00")

        # 7. Today's Activities
        today = date.today()
        today_runs = db.scalars(
            select(CultivationRun)
            .where(
                CultivationRun.farmer_profile_id == fid,
                CultivationRun.is_active == True,
                CultivationRun.is_deleted == False,
            )
            .order_by(CultivationRun.created_at.desc())
        ).all()

        today_activities: List[CRMTodayActivityItem] = []
        active_crop_stage = None
        active_crop_progress = 0
        active_farm_name = None
        active_crop_name = None
        active_season = None

        if today_runs:
            latest_run = today_runs[0]
            farm = latest_run.farm_crop_plan.farm if latest_run.farm_crop_plan else None
            crop = latest_run.farm_crop_plan.crop if latest_run.farm_crop_plan else None
            active_farm_name = farm.farm_name if farm else None
            active_crop_name = crop.crop_name if crop else None
            active_season = latest_run.farm_crop_plan.season if latest_run.farm_crop_plan else None

            # Calculate progress
            total_stages_count = len([s for s in latest_run.stages if not s.is_deleted])
            completed_stages_count = len([s for s in latest_run.stages if not s.is_deleted and s.status == StageStatus.COMPLETED.value])
            if total_stages_count > 0:
                active_crop_progress = int((completed_stages_count / total_stages_count) * 100)
            
            curr_stage = next((s for s in latest_run.stages if s.stage_order == latest_run.current_stage_order and not s.is_deleted), None)
            active_crop_stage = curr_stage.stage_name if curr_stage else f"Stage {latest_run.current_stage_order}"

            for r in today_runs:
                r_farm = r.farm_crop_plan.farm.farm_name if r.farm_crop_plan and r.farm_crop_plan.farm else "Farm"
                r_crop = r.farm_crop_plan.crop.crop_name if r.farm_crop_plan and r.farm_crop_plan.crop else "Crop"
                for st in r.stages:
                    if not st.is_deleted and st.status in (StageStatus.IN_PROGRESS.value, StageStatus.PENDING.value):
                        w_count = len([w for w in st.worker_logs if not w.is_deleted])
                        today_activities.append(
                            CRMTodayActivityItem(
                                id=st.id,
                                cultivation_id=r.id,
                                farm_name=r_farm,
                                crop_name=r_crop,
                                stage_name=st.stage_name,
                                stage_order=st.stage_order,
                                workers_assigned=w_count,
                                machines_assigned=1 if st.status == StageStatus.IN_PROGRESS.value else 0,
                                status=st.status,
                            )
                        )

        return CRMDashboardSummaryResponse(
            total_farms=total_farms,
            active_crop_plans=active_crop_plans,
            active_cultivations=active_cultivations,
            today_work_count=len(today_activities),
            workers_currently_assigned=workers_assigned,
            machines_currently_assigned=machines_assigned,
            material_purchases_count=purchases_count,
            total_cultivation_cost=total_bills_amount,
            pending_payments_amount=pending_payments,
            completed_payments_amount=completed_payments,
            current_crop_stage=active_crop_stage,
            current_crop_progress_pct=active_crop_progress,
            active_cultivation_farm=active_farm_name,
            active_cultivation_crop=active_crop_name,
            active_cultivation_season=active_season,
            today_activities=today_activities[:10],
        )

    # ==========================================
    # Detailed CRM Record & Cost Analytics
    # ==========================================

    @staticmethod
    def get_cultivation_crm_detail(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> CRMCultivationDetailResponse:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(db, cultivation_id, farmer_profile.id)
        if not run:
            # Check if cultivation_id points directly to a FarmCropPlan owned by this farmer
            plan = FarmCropPlanRepository.get_owned_plan(db, cultivation_id, farmer_profile.id)
            if not plan:
                plan = FarmCropPlanRepository.get_by_id(db, cultivation_id)
                if plan and plan.farm and plan.farm.farmer_profile_id != farmer_profile.id:
                    plan = None

            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation run or crop plan not found")

            farm = plan.farm
            crop = plan.crop
            timeline_events = [
                CRMTimelineEvent(
                    date=plan.planned_start_date or date.today(),
                    title="Crop Cultivation Plan Initialized",
                    stage_name="Planning",
                    event_type="STAGE_STARTED",
                    description=f"Plan configured for {crop.crop_name if crop else 'Crop'} at {farm.farm_name if farm else 'Farm'}. Cultivation operations pending.",
                )
            ]

            return CRMCultivationDetailResponse(
                cultivation_id=plan.id,
                farm_id=farm.id if farm else uuid.UUID(int=0),
                farm_name=farm.farm_name if farm else "Farm",
                crop_id=crop.id if crop else uuid.UUID(int=0),
                crop_name=crop.crop_name if crop else "Crop",
                season=plan.season or "Seasonal",
                land_area=Decimal(str(plan.planned_area or 1.0)),
                land_area_unit=plan.land_area_unit or "ACRE",
                sowing_date=plan.planned_start_date or date.today(),
                target_harvest_date=plan.planned_end_date,
                current_stage_order=1,
                current_stage_name="Planning / Not Started",
                overall_progress_pct=0,
                status="PLANNED",
                total_cost=Decimal("0.00"),
                total_paid=Decimal("0.00"),
                total_pending=Decimal("0.00"),
                worker_count=0,
                machine_count=0,
                purchase_count=0,
                logistics_count=0,
                stages=[],
                timeline_events=timeline_events,
            )

        farm = run.farm_crop_plan.farm if run.farm_crop_plan else None
        crop = run.farm_crop_plan.crop if run.farm_crop_plan else None

        # Build Stage Breakdown
        stage_breakdowns: List[StageCostBreakdown] = []
        total_cost = Decimal("0.00")
        total_paid = Decimal("0.00")
        total_pending = Decimal("0.00")

        timeline_events: List[CRMTimelineEvent] = []

        # Timeline event 1: Sowing / Cultivation Start
        timeline_events.append(
            CRMTimelineEvent(
                date=run.sowing_date,
                title="Crop Cultivation Process Initiated",
                stage_name="Planning",
                event_type="STAGE_STARTED",
                description=f"Cultivation started for {crop.crop_name if crop else 'Crop'} at {farm.farm_name if farm else 'Farm'}.",
            )
        )

        for st in run.stages:
            if st.is_deleted:
                continue

            labor_c = Decimal("0.00")
            machine_c = Decimal("0.00")
            material_c = Decimal("0.00")
            other_c = Decimal("0.00")

            # Worker Attendance
            attendances = db.scalars(
                select(WorkerAttendance).where(WorkerAttendance.stage_id == st.id, WorkerAttendance.is_deleted == False)
            ).all()
            for a in attendances:
                labor_c += a.calculated_amount
                timeline_events.append(
                    CRMTimelineEvent(
                        date=a.work_date,
                        title=f"Worker Logged: {a.worker.full_name if a.worker else 'Worker'}",
                        stage_name=st.stage_name,
                        event_type="WORKER_LOGGED",
                        description=f"{a.working_days} days worked @ ₹{a.daily_salary}/day.",
                        cost=a.calculated_amount,
                        payment_status=a.payment_status,
                    )
                )

            # Machine Usage
            usages = db.scalars(
                select(MachineUsage).where(MachineUsage.stage_id == st.id, MachineUsage.is_deleted == False)
            ).all()
            for u in usages:
                machine_c += u.total_cost
                timeline_events.append(
                    CRMTimelineEvent(
                        date=u.usage_date,
                        title=f"Machine Used: {u.machine.machine_name if u.machine else 'Machine'}",
                        stage_name=st.stage_name,
                        event_type="MACHINE_USED",
                        description=f"Machinery applied for {u.hours_used or u.days_used} units.",
                        cost=u.total_cost,
                    )
                )

            # Material Purchases
            purchases = db.scalars(
                select(MaterialPurchase).where(MaterialPurchase.stage_id == st.id, MaterialPurchase.is_deleted == False)
            ).all()
            for p in purchases:
                material_c += p.total_amount
                timeline_events.append(
                    CRMTimelineEvent(
                        date=p.purchase_date,
                        title=f"Material Purchase: {p.material_name}",
                        stage_name=st.stage_name,
                        event_type="PURCHASE_MADE",
                        description=f"{p.quantity} {p.unit} from {p.supplier.supplier_name if p.supplier else 'Supplier'}.",
                        cost=p.total_amount,
                        payment_status=p.payment_status,
                    )
                )

            # Line-item expenses
            for exp in st.expenses:
                if not exp.is_deleted:
                    other_c += exp.amount

            st_total = labor_c + machine_c + material_c + other_c
            total_cost += st_total

            # Get stage bill paid/pending if any
            stage_bills = db.scalars(
                select(Bill).where(Bill.stage_id == st.id, Bill.is_deleted == False)
            ).all()
            st_paid = sum([b.paid_amount for b in stage_bills], Decimal("0.00"))
            st_pending = sum([b.pending_amount for b in stage_bills], st_total - st_paid)
            total_paid += st_paid
            total_pending += max(Decimal("0.00"), st_total - st_paid)

            stage_breakdowns.append(
                StageCostBreakdown(
                    stage_order=st.stage_order,
                    stage_name=st.stage_name,
                    status=st.status,
                    labor_cost=labor_c,
                    machine_cost=machine_c,
                    material_cost=material_c,
                    other_cost=other_c,
                    total_stage_cost=st_total,
                    paid_amount=st_paid,
                    pending_amount=st_pending,
                )
            )

        # Logistics
        logistics_items = db.scalars(
            select(Logistics).where(Logistics.cultivation_id == run.id, Logistics.is_deleted == False)
        ).all()
        for log_entry in logistics_items:
            timeline_events.append(
                CRMTimelineEvent(
                    date=log_entry.pickup_date.date() if isinstance(log_entry.pickup_date, datetime) else date.today(),
                    title=f"Logistics Dispatch: {log_entry.destination}",
                    stage_name="Harvest & Logistics",
                    event_type="LOGISTICS_DISPATCHED",
                    description=f"{log_entry.quantity_transported} {log_entry.quantity_unit} transported via vehicle {log_entry.vehicle_number}.",
                    cost=log_entry.total_logistics_cost,
                    payment_status=log_entry.status,
                )
            )

        # Sort timeline events chronologically
        timeline_events.sort(key=lambda x: x.date)

        total_stages = len(stage_breakdowns)
        completed_stages = len([s for s in stage_breakdowns if s.status == StageStatus.COMPLETED.value])
        overall_progress = int((completed_stages / total_stages) * 100) if total_stages > 0 else 0

        curr_stage_name = next(
            (s.stage_name for s in stage_breakdowns if s.stage_order == run.current_stage_order),
            f"Stage {run.current_stage_order}",
        )

        return CRMCultivationDetailResponse(
            cultivation_id=run.id,
            farm_id=farm.id if farm else uuid.UUID(int=0),
            farm_name=farm.farm_name if farm else "Farm",
            crop_id=crop.id if crop else uuid.UUID(int=0),
            crop_name=crop.crop_name if crop else "Crop",
            season=run.farm_crop_plan.season if run.farm_crop_plan else "Seasonal",
            land_area=Decimal(str(run.land_area or (run.farm_crop_plan.planned_area if run.farm_crop_plan else 1.0))),
            land_area_unit=run.land_area_unit or "ACRE",
            sowing_date=run.sowing_date,
            target_harvest_date=run.target_harvest_date,
            current_stage_order=run.current_stage_order,
            current_stage_name=curr_stage_name,
            overall_progress_pct=overall_progress,
            status="IN_PROGRESS" if run.is_active else "COMPLETED",
            total_cost=total_cost,
            total_paid=total_paid,
            total_pending=total_pending,
            worker_count=len(db.scalars(select(WorkerAttendance.worker_id).where(WorkerAttendance.cultivation_id == run.id)).all()),
            machine_count=len(db.scalars(select(MachineUsage.machine_id).where(MachineUsage.cultivation_id == run.id)).all()),
            purchase_count=len(db.scalars(select(MaterialPurchase.id).where(MaterialPurchase.cultivation_id == run.id)).all()),
            logistics_count=len(logistics_items),
            stages=stage_breakdowns,
            timeline_events=timeline_events,
        )

    # ==========================================
    # Cost Dashboard & Reports
    # ==========================================

    @staticmethod
    def get_crop_cost_summary(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> CropCostSummaryResponse:
        crm_detail = FarmerCRMService.get_cultivation_crm_detail(db, current_user, cultivation_id)
        
        labor_tot = sum([s.labor_cost for s in crm_detail.stages], Decimal("0.00"))
        machine_tot = sum([s.machine_cost for s in crm_detail.stages], Decimal("0.00"))
        material_tot = sum([s.material_cost for s in crm_detail.stages], Decimal("0.00"))
        other_tot = sum([s.other_cost for s in crm_detail.stages], Decimal("0.00"))
        
        # Logistics total
        log_tot = db.scalar(
            select(func.sum(Logistics.total_logistics_cost)).where(
                Logistics.cultivation_id == crm_detail.cultivation_id,
                Logistics.is_deleted == False,
            )
        ) or Decimal("0.00")

        total_cult_cost = labor_tot + machine_tot + material_tot + other_tot + log_tot
        area = crm_detail.land_area if crm_detail.land_area > 0 else Decimal("1.00")
        cost_per_unit = (total_cult_cost / area) if area > Decimal("0.00") else Decimal("0.00")

        return CropCostSummaryResponse(
            cultivation_id=crm_detail.cultivation_id,
            farm_name=crm_detail.farm_name,
            crop_name=crm_detail.crop_name,
            season=crm_detail.season,
            land_area=crm_detail.land_area,
            land_area_unit=crm_detail.land_area_unit,
            stages=crm_detail.stages,
            total_labor_cost=labor_tot,
            total_machine_cost=machine_tot,
            total_material_cost=material_tot,
            total_logistics_cost=log_tot,
            total_other_cost=other_tot,
            total_cultivation_cost=total_cult_cost,
            cost_per_area_unit=cost_per_unit,
            total_paid_amount=crm_detail.total_paid,
            total_pending_amount=crm_detail.total_pending,
        )

    @staticmethod
    def get_crop_cost_report(
        db: Session,
        current_user: User,
    ) -> List[CropCostReportItem]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        runs = db.scalars(
            select(CultivationRun).where(
                CultivationRun.farmer_profile_id == farmer_profile.id,
                CultivationRun.is_deleted == False,
            )
        ).all()

        report_items = []
        for r in runs:
            summary = FarmerCRMService.get_crop_cost_summary(db, current_user, r.id)
            report_items.append(
                CropCostReportItem(
                    cultivation_id=r.id,
                    farm_name=summary.farm_name,
                    crop_name=summary.crop_name,
                    season=summary.season,
                    land_area=summary.land_area,
                    land_area_unit=summary.land_area_unit,
                    labor_cost=summary.total_labor_cost,
                    machine_cost=summary.total_machine_cost,
                    material_cost=summary.total_material_cost,
                    logistics_cost=summary.total_logistics_cost,
                    other_cost=summary.total_other_cost,
                    total_cost=summary.total_cultivation_cost,
                    cost_per_acre=summary.cost_per_area_unit,
                    paid_amount=summary.total_paid_amount,
                    pending_amount=summary.total_pending_amount,
                )
            )
        return report_items

    @staticmethod
    def get_worker_payment_report(
        db: Session,
        current_user: User,
    ) -> List[WorkerPaymentReportItem]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        workers = FarmerCRMRepository.list_workers(db, farmer_profile.id, limit=200)

        report = []
        for w in workers:
            attendances = db.scalars(
                select(WorkerAttendance).where(
                    WorkerAttendance.worker_id == w.id,
                    WorkerAttendance.is_deleted == False,
                )
            ).all()
            tot_days = sum([a.working_days for a in attendances], Decimal("0.00"))
            tot_salary = sum([a.calculated_amount for a in attendances], Decimal("0.00"))
            paid_salary = sum([a.calculated_amount for a in attendances if a.payment_status == "PAID"], Decimal("0.00"))
            pending_salary = tot_salary - paid_salary

            report.append(
                WorkerPaymentReportItem(
                    worker_id=w.id,
                    worker_code=w.worker_code,
                    worker_name=w.full_name,
                    mobile_number=w.mobile_number,
                    gender=w.gender,
                    skill=w.skill,
                    total_working_days=tot_days,
                    total_salary=tot_salary,
                    paid_amount=paid_salary,
                    pending_amount=pending_salary,
                )
            )
        return report

    @staticmethod
    def get_supplier_purchase_report(
        db: Session,
        current_user: User,
    ) -> List[SupplierPurchaseReportItem]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        suppliers = db.scalars(select(Supplier).where(Supplier.is_deleted == False)).all()

        report = []
        for sup in suppliers:
            purchases = db.scalars(
                select(MaterialPurchase).where(
                    MaterialPurchase.supplier_id == sup.id,
                    MaterialPurchase.farmer_profile_id == farmer_profile.id,
                    MaterialPurchase.is_deleted == False,
                )
            ).all()
            if not purchases:
                continue

            tot_amount = sum([p.total_amount for p in purchases], Decimal("0.00"))
            paid_amount = sum([p.total_amount for p in purchases if p.payment_status == "PAID"], Decimal("0.00"))
            pending_amount = tot_amount - paid_amount

            report.append(
                SupplierPurchaseReportItem(
                    supplier_id=sup.id,
                    supplier_code=sup.supplier_code,
                    supplier_name=sup.supplier_name,
                    phone_number=sup.phone_number,
                    total_purchases_count=len(purchases),
                    total_purchase_amount=tot_amount,
                    paid_amount=paid_amount,
                    pending_amount=pending_amount,
                )
            )
        return report

    @staticmethod
    def get_farm_expense_report(
        db: Session,
        current_user: User,
    ) -> List[FarmExpenseReportItem]:
        farmer_profile = FarmerCRMService._resolve_farmer_profile(db, current_user)
        bills = FarmerCRMRepository.list_bills(db, farmer_profile.id, limit=500)

        cat_totals: Dict[str, Dict[str, Decimal]] = {
            "Labor Wages": {"total": Decimal("0.00"), "paid": Decimal("0.00"), "pending": Decimal("0.00")},
            "Machinery & Fuel": {"total": Decimal("0.00"), "paid": Decimal("0.00"), "pending": Decimal("0.00")},
            "Materials & Inputs": {"total": Decimal("0.00"), "paid": Decimal("0.00"), "pending": Decimal("0.00")},
            "Logistics & Transport": {"total": Decimal("0.00"), "paid": Decimal("0.00"), "pending": Decimal("0.00")},
            "Other Expenses": {"total": Decimal("0.00"), "paid": Decimal("0.00"), "pending": Decimal("0.00")},
        }

        grand_total = Decimal("0.00")
        for b in bills:
            cat = "Other Expenses"
            if b.bill_type == BillType.WORKER_PAYMENT.value or b.recipient_type == "WORKER":
                cat = "Labor Wages"
            elif b.bill_type == BillType.MACHINE_COST.value:
                cat = "Machinery & Fuel"
            elif b.bill_type == BillType.MATERIAL_PURCHASE.value or b.recipient_type == "SUPPLIER":
                cat = "Materials & Inputs"
            elif b.bill_type == BillType.LOGISTICS_COST.value or b.recipient_type == "DRIVER":
                cat = "Logistics & Transport"

            cat_totals[cat]["total"] += b.total_amount
            cat_totals[cat]["paid"] += b.paid_amount
            cat_totals[cat]["pending"] += b.pending_amount
            grand_total += b.total_amount

        result = []
        for cat_name, val in cat_totals.items():
            pct = (val["total"] / grand_total * 100) if grand_total > 0 else Decimal("0.00")
            result.append(
                FarmExpenseReportItem(
                    category=cat_name,
                    total_amount=val["total"],
                    paid_amount=val["paid"],
                    pending_amount=val["pending"],
                    percentage=Decimal(str(round(pct, 1))),
                )
            )
        return result
