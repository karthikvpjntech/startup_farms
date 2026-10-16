import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import RoleEnum, StageStatus, ExpenseCategory, FarmingMethod, WorkerPaymentStatus, NotificationType
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.models.cultivation import CultivationRun, CultivationStage, StageWorkerLog
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
from app.repositories.cultivation_repository import CultivationRepository
from app.schemas.cultivation import (
    CultivationRunCreate,
    CultivationRunStatusUpdate,
    CultivationRunResponse,
    CultivationRunListResponse,
    CultivationStageResponse,
    CultivationStageUpdate,
    CustomStageCreate,
    StageExpenseCreate,
    StageExpenseResponse,
    StageWorkerLogCreate,
    StageWorkerLogResponse,
    StageWorkerPaymentStatusUpdate,
    BulkWorkerLogCreate,
    HarvestYieldUpdate,
    CultivationComparisonResponse,
    ComparisonBreakdownMetric,
    MediaUploadProofRequest,
    MediaUploadProofResponse,
)

logger = logging.getLogger("agri_smart.cultivation_service")


class CultivationService:
    """Service handling cultivation lifecycles, dynamic stages, worker wages, and multi-season analytics."""

    @staticmethod
    def _resolve_farmer_profile(db: Session, current_user: User) -> FarmerProfile:
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
                detail="Farmer profile must be completed before managing cultivations"
            )
        return profile

    @staticmethod
    def _format_run_response(run: CultivationRun) -> CultivationRunResponse:
        farm = run.farm_crop_plan.farm if run.farm_crop_plan else None
        crop = run.farm_crop_plan.crop if run.farm_crop_plan else None

        total_labor_wages = Decimal("0.00")
        total_material_expenses = Decimal("0.00")
        total_machinery_expenses = Decimal("0.00")
        total_pending_wages = Decimal("0.00")
        formatted_stages: List[CultivationStageResponse] = []

        for stage in run.stages:
            if stage.is_deleted:
                continue

            stage_labor_wages = Decimal("0.00")
            stage_expenses_total = Decimal("0.00")
            stage_expenses: List[StageExpenseResponse] = []
            stage_worker_logs: List[StageWorkerLogResponse] = []

            # 1. Process worker wage logs
            if hasattr(stage, "worker_logs") and stage.worker_logs:
                for w in stage.worker_logs:
                    if not w.is_deleted:
                        wage_val = Decimal(str(w.total_wage))
                        stage_labor_wages += wage_val
                        total_labor_wages += wage_val
                        if w.payment_status == WorkerPaymentStatus.PENDING.value or w.payment_status == "PENDING":
                            total_pending_wages += wage_val
                        stage_worker_logs.append(StageWorkerLogResponse.model_validate(w))

            # 2. Process stage line-item expenses
            if hasattr(stage, "expenses") and stage.expenses:
                for exp in stage.expenses:
                    if not exp.is_deleted:
                        exp_amount = Decimal(str(exp.amount))
                        stage_expenses_total += exp_amount
                        if exp.expense_category == ExpenseCategory.LABOR.value:
                            total_labor_wages += exp_amount
                        elif exp.expense_category == ExpenseCategory.INPUT_MATERIAL.value:
                            total_material_expenses += exp_amount
                        elif exp.expense_category == ExpenseCategory.MACHINERY.value:
                            total_machinery_expenses += exp_amount
                        stage_expenses.append(StageExpenseResponse.model_validate(exp))

            stage_total = stage_labor_wages + stage_expenses_total

            formatted_stages.append(
                CultivationStageResponse(
                    id=stage.id,
                    cultivation_id=stage.cultivation_id,
                    stage_order=stage.stage_order,
                    stage_name=stage.stage_name,
                    farming_type=stage.farming_type or run.farming_method or "CONVENTIONAL",
                    status=stage.status,
                    start_date=stage.start_date,
                    completed_date=stage.completed_date,
                    expenses=stage_expenses,
                    worker_logs=stage_worker_logs,
                    total_labor_wages=stage_labor_wages,
                    total_expenses=stage_total,
                )
            )

        total_expenses = total_labor_wages + total_material_expenses + total_machinery_expenses
        gross_rev = Decimal(str(run.gross_revenue)) if run.gross_revenue is not None else None
        net_profit = (gross_rev - total_expenses) if gross_rev is not None else None
        net_result_val = net_profit
        net_status = "SURPLUS" if (net_result_val is not None and net_result_val > 0) else ("DEFICIT" if (net_result_val is not None and net_result_val < 0) else "BREAK_EVEN" if net_result_val is not None else None)

        return CultivationRunResponse(
            id=run.id,
            farm_crop_plan_id=run.farm_crop_plan_id,
            farm_id=farm.id if farm else uuid.UUID(int=0),
            crop_id=crop.id if crop else uuid.UUID(int=0),
            crop_name=crop.crop_name if crop else "Unknown Crop",
            farm_name=farm.farm_name if farm else "Unknown Farm",
            farm_code=farm.farm_code if farm else "FARM-000000",
            sowing_date=run.sowing_date,
            maturity_days=run.maturity_days,
            target_harvest_date=run.target_harvest_date,
            current_stage_order=run.current_stage_order,
            farming_method=run.farming_method or "CONVENTIONAL",
            season_year=run.season_year,
            land_area=Decimal(str(run.land_area)) if run.land_area is not None else None,
            land_area_unit=run.land_area_unit or "ACRE",
            yield_quantity=Decimal(str(run.yield_quantity)) if run.yield_quantity is not None else None,
            yield_unit=run.yield_unit or "Bags / மூட்டை",
            selling_price_per_unit=Decimal(str(run.selling_price_per_unit)) if run.selling_price_per_unit is not None else None,
            gross_revenue=gross_rev,
            is_active=run.is_active,
            is_deleted=run.is_deleted,
            stages=formatted_stages,
            total_expenses=total_expenses,
            total_labor_wages=total_labor_wages,
            total_material_expenses=total_material_expenses,
            total_machinery_expenses=total_machinery_expenses,
            total_pending_wages=total_pending_wages,
            net_profit=net_profit,
            net_result=net_result_val,
            net_result_status=net_status,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def start_cultivation(
        db: Session,
        current_user: User,
        request: CultivationRunCreate,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)

        # 1. Verify FarmCropPlan belongs to farmer profile
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=request.farm_crop_plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found or unowned",
            )
        if not plan.is_active or plan.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start cultivation on an inactive or deleted crop plan",
            )

        sowing_date = request.sowing_date or date.today()
        maturity_days = request.maturity_days or 90
        farming_method = request.farming_method.value if request.farming_method else "CONVENTIONAL"

        run = CultivationRepository.create_run(
            db=db,
            farmer_profile_id=farmer_profile.id,
            plan=plan,
            sowing_date=sowing_date,
            maturity_days=maturity_days,
            created_by=current_user.id,
            farming_method=farming_method,
            season_year=request.season_year,
            land_area=request.land_area,
            land_area_unit=request.land_area_unit or "ACRE",
            custom_stages=request.custom_stages,
        )
        logger.info("Cultivation run %s started for plan %s (Method: %s)", run.id, plan.id, farming_method)
        return CultivationService._format_run_response(run)

    @staticmethod
    def list_cultivations(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> CultivationRunListResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size

        runs = CultivationRepository.list_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            is_active=is_active,
            search=search,
            include_deleted=False,
        )
        total = CultivationRepository.count_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            is_active=is_active,
            include_deleted=False,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = [CultivationService._format_run_response(r) for r in runs]
        return CultivationRunListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    def get_cultivation_detail(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )
        return CultivationService._format_run_response(run)

    @staticmethod
    def update_status(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
        request: CultivationRunStatusUpdate,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )
        updated_run = CultivationRepository.update_status(
            db=db,
            run=run,
            is_active=request.is_active,
            updated_by=current_user.id,
        )
        return CultivationService._format_run_response(updated_run)

    @staticmethod
    def delete_cultivation(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )
        deleted_run = CultivationRepository.soft_delete_run(
            db=db,
            run=run,
            deleted_by=current_user.id,
        )
        return CultivationService._format_run_response(deleted_run)

    # ==========================================
    # Dynamic Custom Stages Service Logic
    # ==========================================

    @staticmethod
    def create_custom_stage(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
        request: CustomStageCreate,
    ) -> CultivationStageResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )

        farming_type = request.farming_type.value if request.farming_type else run.farming_method
        status_val = request.status.value if request.status else StageStatus.PENDING.value

        stage = CultivationRepository.create_custom_stage(
            db=db,
            cultivation=run,
            stage_name=request.stage_name,
            stage_order=request.stage_order,
            farming_type=farming_type,
            status=status_val,
            created_by=current_user.id,
        )
        logger.info("Custom stage '%s' created for run %s", stage.stage_name, run.id)
        return CultivationStageResponse(
            id=stage.id,
            cultivation_id=stage.cultivation_id,
            stage_order=stage.stage_order,
            stage_name=stage.stage_name,
            farming_type=stage.farming_type,
            status=stage.status,
            start_date=stage.start_date,
            completed_date=stage.completed_date,
            expenses=[],
            worker_logs=[],
            total_labor_wages=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
        )

    @staticmethod
    def update_stage(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: CultivationStageUpdate,
    ) -> CultivationStageResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        updated_stage = CultivationRepository.update_stage(
            db=db,
            stage=stage,
            stage_name=request.stage_name,
            status=request.status.value if request.status else None,
            farming_type=request.farming_type.value if request.farming_type else None,
            start_date=request.start_date,
            completed_date=request.completed_date,
            updated_by=current_user.id,
        )
        return CultivationStageResponse(
            id=updated_stage.id,
            cultivation_id=updated_stage.cultivation_id,
            stage_order=updated_stage.stage_order,
            stage_name=updated_stage.stage_name,
            farming_type=updated_stage.farming_type,
            status=updated_stage.status,
            start_date=updated_stage.start_date,
            completed_date=updated_stage.completed_date,
            expenses=[StageExpenseResponse.model_validate(e) for e in updated_stage.expenses if not e.is_deleted],
            worker_logs=[StageWorkerLogResponse.model_validate(w) for w in updated_stage.worker_logs if not w.is_deleted],
            total_labor_wages=sum([Decimal(str(w.total_wage)) for w in updated_stage.worker_logs if not w.is_deleted]),
            total_expenses=sum([Decimal(str(e.amount)) for e in updated_stage.expenses if not e.is_deleted]),
        )

    @staticmethod
    def delete_stage(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> CultivationStageResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        deleted_stage = CultivationRepository.delete_stage(db, stage, deleted_by=current_user.id)
        return CultivationStageResponse(
            id=deleted_stage.id,
            cultivation_id=deleted_stage.cultivation_id,
            stage_order=deleted_stage.stage_order,
            stage_name=deleted_stage.stage_name,
            farming_type=deleted_stage.farming_type,
            status=deleted_stage.status,
            start_date=deleted_stage.start_date,
            completed_date=deleted_stage.completed_date,
            expenses=[],
            worker_logs=[],
            total_labor_wages=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
        )

    @staticmethod
    def list_stages(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
    ) -> List[CultivationStageResponse]:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )
        stages = CultivationRepository.list_stages(db=db, cultivation_id=cultivation_id)
        results = []
        for stage in stages:
            expenses = [
                StageExpenseResponse.model_validate(e)
                for e in stage.expenses
                if not e.is_deleted
            ]
            worker_logs = [
                StageWorkerLogResponse.model_validate(w)
                for w in stage.worker_logs
                if not w.is_deleted
            ]
            labor_wages_sum = sum([Decimal(str(w.total_wage)) for w in stage.worker_logs if not w.is_deleted], Decimal("0.00"))
            expenses_sum = sum([Decimal(str(e.amount)) for e in stage.expenses if not e.is_deleted], Decimal("0.00"))

            results.append(
                CultivationStageResponse(
                    id=stage.id,
                    cultivation_id=stage.cultivation_id,
                    stage_order=stage.stage_order,
                    stage_name=stage.stage_name,
                    farming_type=stage.farming_type or "CONVENTIONAL",
                    status=stage.status,
                    start_date=stage.start_date,
                    completed_date=stage.completed_date,
                    expenses=expenses,
                    worker_logs=worker_logs,
                    total_labor_wages=labor_wages_sum,
                    total_expenses=labor_wages_sum + expenses_sum,
                )
            )
        return results

    @staticmethod
    def complete_and_next_stage(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )
        if stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this cultivation stage",
            )
        if stage.status == StageStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This stage is already marked as completed",
            )

        updated_run = CultivationRepository.advance_stage(
            db=db,
            current_stage=stage,
            updated_by=current_user.id,
        )
        logger.info("Stage %s advanced for run %s", stage_id, updated_run.id)
        return CultivationService._format_run_response(updated_run)

    # ==========================================
    # Worker Daily Wages & Attendance Logic
    # ==========================================

    @staticmethod
    def add_worker_log(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: StageWorkerLogCreate,
    ) -> StageWorkerLogResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        data = request.model_dump()
        data["payment_status"] = request.payment_status.value if request.payment_status else "PENDING"
        worker_log = CultivationRepository.add_worker_log(
            db=db,
            stage=stage,
            worker_data=data,
            created_by=current_user.id,
        )
        logger.info("Worker wage log created: %s for stage %s", worker_log.id, stage_id)
        return StageWorkerLogResponse.model_validate(worker_log)

    @staticmethod
    def bulk_add_worker_logs(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: BulkWorkerLogCreate,
    ) -> List[StageWorkerLogResponse]:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        workers_data = []
        for w in request.workers:
            d = w.model_dump()
            d["payment_status"] = w.payment_status.value if w.payment_status else "PENDING"
            workers_data.append(d)

        logs = CultivationRepository.bulk_add_worker_logs(
            db=db,
            stage=stage,
            workers_list=workers_data,
            created_by=current_user.id,
        )
        return [StageWorkerLogResponse.model_validate(l) for l in logs]

    @staticmethod
    def list_stage_worker_logs(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> List[StageWorkerLogResponse]:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        logs = CultivationRepository.list_stage_worker_logs(db=db, stage_id=stage_id, include_deleted=False)
        return [StageWorkerLogResponse.model_validate(l) for l in logs]

    @staticmethod
    def update_worker_payment_status(
        db: Session,
        current_user: User,
        worker_log_id: uuid.UUID,
        request: StageWorkerPaymentStatusUpdate,
    ) -> StageWorkerLogResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        worker_log = CultivationRepository.get_worker_log_by_id(db, worker_log_id)
        if not worker_log or worker_log.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker log not found",
            )

        updated = CultivationRepository.update_worker_payment_status(
            db=db,
            worker_log=worker_log,
            payment_status=request.payment_status.value,
            updated_by=current_user.id,
        )
        return StageWorkerLogResponse.model_validate(updated)

    @staticmethod
    def delete_worker_log(
        db: Session,
        current_user: User,
        worker_log_id: uuid.UUID,
    ) -> StageWorkerLogResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        worker_log = CultivationRepository.get_worker_log_by_id(db, worker_log_id)
        if not worker_log or worker_log.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker log not found",
            )

        deleted = CultivationRepository.soft_delete_worker_log(db, worker_log, deleted_by=current_user.id)
        return StageWorkerLogResponse.model_validate(deleted)

    # ==========================================
    # Stage Expense Logic
    # ==========================================

    @staticmethod
    def log_expense(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: StageExpenseCreate,
    ) -> StageExpenseResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )

        data = request.model_dump()
        data["expense_category"] = request.expense_category.value
        data["payment_mode"] = request.payment_mode.value if request.payment_mode else "CASH"
        data["machinery_type"] = request.machinery_type.value if request.machinery_type else None

        expense = CultivationRepository.add_expense(
            db=db,
            stage=stage,
            expense_data=data,
            created_by=current_user.id,
        )
        logger.info("Stage expense logged: ₹%s under stage %s", expense.amount, stage.id)
        return StageExpenseResponse.model_validate(expense)

    @staticmethod
    def list_stage_expenses(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
    ) -> List[StageExpenseResponse]:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        stage = CultivationRepository.get_stage_by_id(db, stage_id)
        if not stage or stage.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found",
            )
        expenses = CultivationRepository.list_stage_expenses(db=db, stage_id=stage_id, include_deleted=False)
        return [StageExpenseResponse.model_validate(e) for e in expenses]

    @staticmethod
    def soft_delete_expense(
        db: Session,
        current_user: User,
        expense_id: uuid.UUID,
    ) -> StageExpenseResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        expense = CultivationRepository.get_expense_by_id(db, expense_id, include_deleted=False)
        if not expense or expense.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stage expense entry not found",
            )

        deleted = CultivationRepository.soft_delete_expense(
            db=db,
            expense=expense,
            deleted_by=current_user.id,
        )
        return StageExpenseResponse.model_validate(deleted)

    @staticmethod
    def add_expense(
        db: Session,
        current_user: User,
        stage_id: uuid.UUID,
        request: StageExpenseCreate,
    ) -> StageExpenseResponse:
        return CultivationService.log_expense(db=db, current_user=current_user, stage_id=stage_id, request=request)

    @staticmethod
    def delete_expense(
        db: Session,
        current_user: User,
        expense_id: uuid.UUID,
    ) -> StageExpenseResponse:
        return CultivationService.soft_delete_expense(db=db, current_user=current_user, expense_id=expense_id)

    @staticmethod
    def restore_expense(
        db: Session,
        current_user: User,
        expense_id: uuid.UUID,
    ) -> StageExpenseResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        expense = CultivationRepository.get_expense_by_id(db, expense_id, include_deleted=True)
        if not expense or expense.cultivation.farmer_profile_id != farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stage expense entry not found",
            )

        restored = CultivationRepository.restore_expense(
            db=db,
            expense=expense,
            updated_by=current_user.id,
        )
        return StageExpenseResponse.model_validate(restored)

    # ==========================================
    # Harvest Metrics & Side-by-Side Comparison
    # ==========================================

    @staticmethod
    def update_harvest_yield(
        db: Session,
        current_user: User,
        cultivation_id: uuid.UUID,
        request: HarvestYieldUpdate,
    ) -> CultivationRunResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)
        run = CultivationRepository.get_by_id(
            db=db,
            cultivation_id=cultivation_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False,
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation run not found",
            )

        updated_run = CultivationRepository.update_harvest_metrics(
            db=db,
            run=run,
            yield_quantity=request.yield_quantity,
            selling_price_per_unit=request.selling_price_per_unit,
            yield_unit=request.yield_unit,
            gross_revenue=request.gross_revenue,
            updated_by=current_user.id,
        )

        # Broadcast Fresh Harvest Alerts to registered customers and buyers (App, SMS, Email)
        try:
            crop = updated_run.farm_crop_plan.crop if updated_run.farm_crop_plan else None
            farm = updated_run.farm_crop_plan.farm if updated_run.farm_crop_plan else None
            crop_title = crop.crop_name if crop else "Produce"
            crop_local = crop.crop_name_local if crop else None
            farmer_name = current_user.full_name or "Farmer"
            farm_name = farm.farm_name if farm else "Verified Farm"
            farm_loc = farm.location or (farm.district if farm else "Tamil Nadu")

            # Fetch registered public customers and buyers
            buyers = list(
                db.execute(
                    select(User).where(
                        User.is_active.is_(True),
                        User.is_deleted.is_(False),
                        User.id != current_user.id
                    ).limit(25)
                ).scalars().all()
            )

            sms_body = (
                f"🌾 Fresh Harvest Alert: Farmer {farmer_name} has recorded {request.yield_quantity} {request.yield_unit} "
                f"of {crop_title}{f' ({crop_local})' if crop_local else ''} from {farm_name} at ₹{request.selling_price_per_unit}/{request.yield_unit}! "
                f"Direct procurement open now: {settings.FRONTEND_URL}/marketplace/produce"
            )

            for buyer in buyers:
                # 1. SMS Dispatch & Audit Log
                if buyer.mobile_number:
                    try:
                        NotificationService.send_sms(
                            db=db,
                            farmer_profile_id=farmer_profile.id,
                            recipient_mobile=buyer.mobile_number,
                            recipient_name=buyer.full_name or "Buyer",
                            message_body=sms_body,
                            recipient_type="CUSTOMER",
                            notification_type=NotificationType.YIELD_HARVEST_ALERT.value,
                            related_entity_type="CULTIVATION_RUN",
                            related_entity_id=updated_run.id,
                        )
                    except Exception as exc:
                        logger.warning("Failed to dispatch harvest SMS to buyer %s: %s", buyer.id, exc)

                # 2. Email Dispatch
                if buyer.email:
                    try:
                        EmailService.send_harvest_yield_email(
                            to_email=buyer.email,
                            customer_name=buyer.full_name or "Valued Buyer",
                            farmer_name=farmer_name,
                            crop_name=crop_title,
                            crop_name_local=crop_local,
                            yield_quantity=str(request.yield_quantity),
                            yield_unit=request.yield_unit,
                            price_per_unit=str(request.selling_price_per_unit),
                            farm_location=farm_loc,
                            farm_name=farm_name,
                        )
                    except Exception as exc:
                        logger.warning("Failed to dispatch harvest Email to buyer %s: %s", buyer.id, exc)

            logger.info("Harvest yield broadcast completed for %s (%d buyers notified)", crop_title, len(buyers))
        except Exception as err:
            logger.warning("Harvest notification broadcast encounter non-fatal error: %s", err)

        return CultivationService._format_run_response(updated_run)

    @staticmethod
    def get_comparison_report(
        db: Session,
        current_user: User,
        conventional_run_id: Optional[uuid.UUID] = None,
        organic_run_id: Optional[uuid.UUID] = None,
    ) -> CultivationComparisonResponse:
        farmer_profile = CultivationService._resolve_farmer_profile(db, current_user)

        conv_run: Optional[CultivationRun] = None
        org_run: Optional[CultivationRun] = None

        if conventional_run_id:
            conv_run = CultivationRepository.get_by_id(db, conventional_run_id, farmer_profile.id)
        if organic_run_id:
            org_run = CultivationRepository.get_by_id(db, organic_run_id, farmer_profile.id)

        # Fallback to any recent runs if not specified
        if not conv_run or not org_run:
            all_runs = CultivationRepository.list_by_farmer(db, farmer_profile.id, skip=0, limit=10)
            for r in all_runs:
                if not conv_run and r.farming_method in ("CONVENTIONAL", None):
                    conv_run = r
                elif not org_run and r.farming_method in ("ORGANIC", "NATURAL"):
                    org_run = r

        # If no authentic comparison records exist in database
        if not conv_run and not org_run:
            return CultivationComparisonResponse(
                conventional_run=None,
                organic_run=None,
                breakdown_metrics=[],
                total_conventional_expense=Decimal("0.00"),
                total_organic_expense=Decimal("0.00"),
                expense_savings=Decimal("0.00"),
                conventional_gross_revenue=Decimal("0.00"),
                organic_gross_revenue=Decimal("0.00"),
                conventional_net_profit=Decimal("0.00"),
                organic_net_profit=Decimal("0.00"),
                net_profit_gain=Decimal("0.00"),
                has_previous_data=False,
                message="No previous-year data available.",
            )

        conv_formatted = CultivationService._format_run_response(conv_run) if conv_run else None
        org_formatted = CultivationService._format_run_response(org_run) if org_run else None

        # Build comparison metrics strictly from real database records
        conv_land = conv_formatted.land_area if (conv_formatted and conv_formatted.land_area) else Decimal("0.00")
        org_land = org_formatted.land_area if (org_formatted and org_formatted.land_area) else Decimal("0.00")

        conv_tillage = Decimal("0.00")
        org_tillage = Decimal("0.00")
        if conv_formatted:
            t_stages = [s for s in conv_formatted.stages if any(k in s.stage_name for k in ["உழவு", "Land", "Planting", "நடவு", "Preparation"])]
            if t_stages:
                conv_tillage = sum([s.total_expenses for s in t_stages], Decimal("0.00"))
        if org_formatted:
            t_stages = [s for s in org_formatted.stages if any(k in s.stage_name for k in ["உழவு", "Land", "Planting", "நடவு", "Preparation"])]
            if t_stages:
                org_tillage = sum([s.total_expenses for s in t_stages], Decimal("0.00"))

        conv_weeding = Decimal("0.00")
        org_weeding = Decimal("0.00")
        if conv_formatted:
            w_stages = [s for s in conv_formatted.stages if any(k in s.stage_name for k in ["பில்லு", "களை", "Weeding", "De-weed"])]
            if w_stages:
                conv_weeding = sum([s.total_expenses for s in w_stages], Decimal("0.00"))
        if org_formatted:
            w_stages = [s for s in org_formatted.stages if any(k in s.stage_name for k in ["பில்லு", "களை", "Weeding", "De-weed"])]
            if w_stages:
                org_weeding = sum([s.total_expenses for s in w_stages], Decimal("0.00"))

        conv_fertilizer = Decimal("0.00")
        org_fertilizer = Decimal("0.00")
        if conv_formatted:
            f_stages = [s for s in conv_formatted.stages if any(k in s.stage_name for k in ["மருந்து", "உரம்", "Fertilization", "Fertilizer", "Spray"])]
            if f_stages:
                conv_fertilizer = sum([s.total_expenses for s in f_stages], Decimal("0.00"))
        if org_formatted:
            f_stages = [s for s in org_formatted.stages if any(k in s.stage_name for k in ["மருந்து", "உரம்", "Fertilization", "Fertilizer", "Spray"])]
            if f_stages:
                org_fertilizer = sum([s.total_expenses for s in f_stages], Decimal("0.00"))

        conv_harvest = Decimal("0.00")
        org_harvest = Decimal("0.00")
        if conv_formatted:
            h_stages = [s for s in conv_formatted.stages if any(k in s.stage_name for k in ["அறுவடை", "Harvest", "மூட்டை", "தாள்", "Bagging"])]
            if h_stages:
                conv_harvest = sum([s.total_expenses for s in h_stages], Decimal("0.00"))
        if org_formatted:
            h_stages = [s for s in org_formatted.stages if any(k in s.stage_name for k in ["அறுவடை", "Harvest", "மூட்டை", "தாள்", "Bagging"])]
            if h_stages:
                org_harvest = sum([s.total_expenses for s in h_stages], Decimal("0.00"))

        total_conv_exp = conv_formatted.total_expenses if (conv_formatted and conv_formatted.total_expenses > 0) else (conv_tillage + conv_weeding + conv_fertilizer + conv_harvest)
        total_org_exp = org_formatted.total_expenses if (org_formatted and org_formatted.total_expenses > 0) else (org_tillage + org_weeding + org_fertilizer + org_harvest)
        expense_savings = total_conv_exp - total_org_exp

        conv_gross = conv_formatted.gross_revenue if (conv_formatted and conv_formatted.gross_revenue) else Decimal("0.00")
        org_gross = org_formatted.gross_revenue if (org_formatted and org_formatted.gross_revenue) else Decimal("0.00")

        conv_net = conv_gross - total_conv_exp
        org_net = org_gross - total_org_exp
        net_gain = org_net - conv_net

        metrics = [
            ComparisonBreakdownMetric(
                category_key="LAND_AREA",
                title_en="Land Area",
                title_ta="நிலப் பரப்பு",
                conventional_val=conv_land,
                organic_val=org_land,
                diff_val=org_land - conv_land,
                unit="Acres / ஏக்கர்",
                notes_conventional=f"{conv_land} Acres" if conv_land > 0 else "N/A",
                notes_organic=f"{org_land} Acres" if org_land > 0 else "N/A",
            ),
            ComparisonBreakdownMetric(
                category_key="TILLAGE_PLANTING",
                title_en="Tillage & Planting Labor",
                title_ta="மொத்த உழவு & நடவு கூலி",
                conventional_val=conv_tillage,
                organic_val=org_tillage,
                diff_val=org_tillage - conv_tillage,
                unit="₹",
                notes_conventional="Conventional tillage & planting",
                notes_organic="Organic nursery & planting",
            ),
            ComparisonBreakdownMetric(
                category_key="WEEDING",
                title_en="De-weeding & Maintenance",
                title_ta="பில்லு புடுங்குறது (களை எடுத்தல்)",
                conventional_val=conv_weeding,
                organic_val=org_weeding,
                diff_val=org_weeding - conv_weeding,
                unit="₹",
                notes_conventional="Conventional weeding",
                notes_organic="Manual weeding",
            ),
            ComparisonBreakdownMetric(
                category_key="INPUT_FERTILIZER_PESTICIDE",
                title_en="Fertilizers & Pesticides",
                title_ta="உரம் & பூச்சி மருந்து செலவு",
                conventional_val=conv_fertilizer,
                organic_val=org_fertilizer,
                diff_val=org_fertilizer - conv_fertilizer,
                unit="₹",
                notes_conventional="Conventional fertilizers/sprays",
                notes_organic="Bio-fertilizers & bio-pesticides",
            ),
            ComparisonBreakdownMetric(
                category_key="HARVEST_BAGGING",
                title_en="Harvesting & Bagging",
                title_ta="அறுவடை & மூட்டை பிடித்தல் கூலி",
                conventional_val=conv_harvest,
                organic_val=org_harvest,
                diff_val=org_harvest - conv_harvest,
                unit="₹",
                notes_conventional="Harvesting & bagging",
                notes_organic="Harvesting & bagging",
            ),
        ]

        return CultivationComparisonResponse(
            conventional_run=conv_formatted,
            organic_run=org_formatted,
            breakdown_metrics=metrics,
            total_conventional_expense=total_conv_exp,
            total_organic_expense=total_org_exp,
            expense_savings=expense_savings,
            conventional_gross_revenue=conv_gross,
            organic_gross_revenue=org_gross,
            conventional_net_profit=conv_net,
            organic_net_profit=org_net,
            net_profit_gain=net_gain,
        )

    @staticmethod
    def generate_media_upload_url(request: MediaUploadProofRequest) -> MediaUploadProofResponse:
        """Generates pre-signed upload URL for bill receipts / proof photos."""
        file_key = f"proofs/{uuid.uuid4()}-{request.filename}"
        mock_upload_url = f"/api/v1/media/upload/{file_key}"
        mock_public_url = f"/uploads/{file_key}"

        return MediaUploadProofResponse(
            upload_url=mock_upload_url,
            public_url=mock_public_url,
            file_key=file_key,
            expires_in_seconds=3600,
        )

