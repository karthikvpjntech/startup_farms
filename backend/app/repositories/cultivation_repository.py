import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.cultivation import CultivationRun, CultivationStage, StageExpense, StageWorkerLog, DEFAULT_CULTIVATION_STAGES
from app.models.crop_stage import CropCultivationStage
from app.models.enums import StageStatus, WorkerPaymentStatus, FarmingMethod
from app.models.farm_crop_plan import FarmCropPlan


class CultivationRepository:
    """Data access methods for Cultivation Runs, Dynamic Stages, Itemized Expenses, and Worker Wages."""

    @staticmethod
    def create_run(
        db: Session,
        farmer_profile_id: uuid.UUID,
        plan: FarmCropPlan,
        sowing_date: date,
        maturity_days: int,
        created_by: uuid.UUID,
        farming_method: str = "CONVENTIONAL",
        season_year: Optional[str] = None,
        land_area: Optional[Decimal] = None,
        land_area_unit: str = "ACRE",
        custom_stages: Optional[List[str]] = None,
    ) -> CultivationRun:
        target_harvest = sowing_date + timedelta(days=maturity_days)
        
        run = CultivationRun(
            id=uuid.uuid4(),
            farm_crop_plan_id=plan.id,
            farmer_profile_id=farmer_profile_id,
            sowing_date=sowing_date,
            maturity_days=maturity_days,
            target_harvest_date=target_harvest,
            current_stage_order=1,
            farming_method=farming_method,
            season_year=season_year or f"{sowing_date.year} Season",
            land_area=land_area or (Decimal(str(plan.allocated_area)) if hasattr(plan, 'allocated_area') and plan.allocated_area else Decimal("1.0")),
            land_area_unit=land_area_unit,
            is_active=True,
            is_deleted=False,
            created_by=created_by,
        )
        db.add(run)
        db.flush()

        # Determine stages to seed:
        # 1. If custom stage names provided, use them
        # 2. Else check if crop has master agronomy stages configured in CropCultivationStage
        # 3. Else fallback to DEFAULT_CULTIVATION_STAGES
        if custom_stages and len(custom_stages) > 0:
            stages_to_create = [(i + 1, name) for i, name in enumerate(custom_stages)]
        else:
            master_stages = (
                db.query(CropCultivationStage)
                .filter(
                    CropCultivationStage.crop_id == plan.crop_id,
                    CropCultivationStage.is_active == True,
                    CropCultivationStage.is_deleted == False,
                )
                .order_by(CropCultivationStage.stage_order.asc())
                .all()
            )
            if master_stages and len(master_stages) > 0:
                stages_to_create = [(s.stage_order, s.stage_name) for s in master_stages]
            else:
                stages_to_create = DEFAULT_CULTIVATION_STAGES

        for order, name in stages_to_create:
            stage_status = StageStatus.IN_PROGRESS.value if order == 1 else StageStatus.PENDING.value
            stage_start = sowing_date if order == 1 else None

            stage = CultivationStage(
                id=uuid.uuid4(),
                cultivation_id=run.id,
                stage_order=order,
                stage_name=name,
                farming_type=farming_method,
                status=stage_status,
                start_date=stage_start,
                created_by=created_by,
            )
            db.add(stage)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_by_id(
        db: Session,
        cultivation_id: uuid.UUID,
        farmer_profile_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[CultivationRun]:
        query = (
            db.query(CultivationRun)
            .options(
                joinedload(CultivationRun.stages).joinedload(CultivationStage.expenses),
                joinedload(CultivationRun.stages).joinedload(CultivationStage.worker_logs),
                joinedload(CultivationRun.farm_crop_plan),
            )
            .filter(
                or_(
                    CultivationRun.id == cultivation_id,
                    CultivationRun.farm_crop_plan_id == cultivation_id,
                ),
                CultivationRun.farmer_profile_id == farmer_profile_id,
            )
        )
        if not include_deleted:
            query = query.filter(CultivationRun.is_deleted == False)  # noqa: E712
        return query.order_by(CultivationRun.is_active.desc(), CultivationRun.created_at.desc()).first()

    @staticmethod
    def list_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[CultivationRun]:
        query = (
            db.query(CultivationRun)
            .options(
                joinedload(CultivationRun.stages).joinedload(CultivationStage.expenses),
                joinedload(CultivationRun.stages).joinedload(CultivationStage.worker_logs),
                joinedload(CultivationRun.farm_crop_plan),
            )
            .filter(CultivationRun.farmer_profile_id == farmer_profile_id)
        )
        if not include_deleted:
            query = query.filter(CultivationRun.is_deleted == False)  # noqa: E712
        if is_active is not None:
            query = query.filter(CultivationRun.is_active == is_active)

        return (
            query.order_by(CultivationRun.is_active.desc(), CultivationRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> int:
        query = db.query(func.count(CultivationRun.id)).filter(
            CultivationRun.farmer_profile_id == farmer_profile_id
        )
        if not include_deleted:
            query = query.filter(CultivationRun.is_deleted == False)  # noqa: E712
        if is_active is not None:
            query = query.filter(CultivationRun.is_active == is_active)
        return query.scalar() or 0

    @staticmethod
    def update_status(
        db: Session,
        run: CultivationRun,
        is_active: bool,
        updated_by: uuid.UUID,
    ) -> CultivationRun:
        run.is_active = is_active
        run.updated_by = updated_by
        run.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def soft_delete_run(
        db: Session,
        run: CultivationRun,
        deleted_by: uuid.UUID,
    ) -> CultivationRun:
        run.is_deleted = True
        run.deleted_at = datetime.now(timezone.utc)
        run.deleted_by = deleted_by
        run.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run

    # ==========================================
    # Dynamic Stages Data Access
    # ==========================================

    @staticmethod
    def create_custom_stage(
        db: Session,
        cultivation: CultivationRun,
        stage_name: str,
        stage_order: Optional[int] = None,
        farming_type: str = "CONVENTIONAL",
        status: str = "PENDING",
        created_by: uuid.UUID = None,
    ) -> CultivationStage:
        if stage_order is None:
            max_order = db.query(func.max(CultivationStage.stage_order)).filter(
                CultivationStage.cultivation_id == cultivation.id,
                CultivationStage.is_deleted == False,  # noqa: E712
            ).scalar() or 0
            stage_order = max_order + 1

        stage = CultivationStage(
            id=uuid.uuid4(),
            cultivation_id=cultivation.id,
            stage_order=stage_order,
            stage_name=stage_name,
            farming_type=farming_type,
            status=status,
            created_by=created_by,
        )
        db.add(stage)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def get_stage_by_id(db: Session, stage_id: uuid.UUID) -> Optional[CultivationStage]:
        return (
            db.query(CultivationStage)
            .options(
                joinedload(CultivationStage.cultivation),
                joinedload(CultivationStage.expenses),
                joinedload(CultivationStage.worker_logs),
            )
            .filter(CultivationStage.id == stage_id, CultivationStage.is_deleted == False)  # noqa: E712
            .first()
        )

    @staticmethod
    def list_stages(db: Session, cultivation_id: uuid.UUID) -> List[CultivationStage]:
        return (
            db.query(CultivationStage)
            .options(
                joinedload(CultivationStage.expenses),
                joinedload(CultivationStage.worker_logs),
            )
            .filter(CultivationStage.cultivation_id == cultivation_id, CultivationStage.is_deleted == False)  # noqa: E712
            .order_by(CultivationStage.stage_order.asc())
            .all()
        )

    @staticmethod
    def update_stage(
        db: Session,
        stage: CultivationStage,
        stage_name: Optional[str] = None,
        status: Optional[str] = None,
        farming_type: Optional[str] = None,
        start_date: Optional[date] = None,
        completed_date: Optional[date] = None,
        updated_by: uuid.UUID = None,
    ) -> CultivationStage:
        if stage_name is not None:
            stage.stage_name = stage_name
        if status is not None:
            stage.status = status
        if farming_type is not None:
            stage.farming_type = farming_type
        if start_date is not None:
            stage.start_date = start_date
        if completed_date is not None:
            stage.completed_date = completed_date

        stage.updated_by = updated_by
        stage.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def delete_stage(
        db: Session,
        stage: CultivationStage,
        deleted_by: uuid.UUID,
    ) -> CultivationStage:
        stage.is_deleted = True
        stage.updated_by = deleted_by
        stage.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def advance_stage(
        db: Session,
        current_stage: CultivationStage,
        updated_by: uuid.UUID,
    ) -> CultivationRun:
        today = date.today()
        current_stage.status = StageStatus.COMPLETED.value
        current_stage.completed_date = today
        current_stage.updated_by = updated_by
        current_stage.updated_at = datetime.now(timezone.utc)

        # Look for the immediate next stage
        next_stage = (
            db.query(CultivationStage)
            .filter(
                CultivationStage.cultivation_id == current_stage.cultivation_id,
                CultivationStage.stage_order == current_stage.stage_order + 1,
                CultivationStage.is_deleted == False,  # noqa: E712
            )
            .first()
        )

        run = current_stage.cultivation
        if next_stage:
            next_stage.status = StageStatus.IN_PROGRESS.value
            next_stage.start_date = today
            next_stage.updated_by = updated_by
            next_stage.updated_at = datetime.now(timezone.utc)
            run.current_stage_order = next_stage.stage_order
        else:
            # Reached end of all stages
            run.current_stage_order = current_stage.stage_order

        run.updated_by = updated_by
        run.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(run)
        return run

    # ==========================================
    # Worker Wage Logs Data Access
    # ==========================================

    @staticmethod
    def add_worker_log(
        db: Session,
        stage: CultivationStage,
        worker_data: dict,
        created_by: uuid.UUID,
    ) -> StageWorkerLog:
        days_worked = Decimal(str(worker_data["days_worked"]))
        daily_wage = Decimal(str(worker_data["daily_wage"]))
        total_wage = days_worked * daily_wage

        worker_log = StageWorkerLog(
            id=uuid.uuid4(),
            stage_id=stage.id,
            cultivation_id=stage.cultivation_id,
            worker_name=worker_data["worker_name"],
            worker_id=worker_data.get("worker_id"),
            days_worked=days_worked,
            daily_wage=daily_wage,
            total_wage=total_wage,
            payment_status=worker_data.get("payment_status", "PENDING"),
            notes=worker_data.get("notes"),
            created_by=created_by,
        )
        db.add(worker_log)
        db.commit()
        db.refresh(worker_log)
        return worker_log

    @staticmethod
    def bulk_add_worker_logs(
        db: Session,
        stage: CultivationStage,
        workers_list: List[dict],
        created_by: uuid.UUID,
    ) -> List[StageWorkerLog]:
        created_logs = []
        for worker_data in workers_list:
            days_worked = Decimal(str(worker_data["days_worked"]))
            daily_wage = Decimal(str(worker_data["daily_wage"]))
            total_wage = days_worked * daily_wage

            worker_log = StageWorkerLog(
                id=uuid.uuid4(),
                stage_id=stage.id,
                cultivation_id=stage.cultivation_id,
                worker_name=worker_data["worker_name"],
                worker_id=worker_data.get("worker_id"),
                days_worked=days_worked,
                daily_wage=daily_wage,
                total_wage=total_wage,
                payment_status=worker_data.get("payment_status", "PENDING"),
                notes=worker_data.get("notes"),
                created_by=created_by,
            )
            db.add(worker_log)
            created_logs.append(worker_log)

        db.commit()
        for log in created_logs:
            db.refresh(log)
        return created_logs

    @staticmethod
    def get_worker_log_by_id(
        db: Session,
        worker_log_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[StageWorkerLog]:
        query = (
            db.query(StageWorkerLog)
            .options(joinedload(StageWorkerLog.cultivation), joinedload(StageWorkerLog.stage))
            .filter(StageWorkerLog.id == worker_log_id)
        )
        if not include_deleted:
            query = query.filter(StageWorkerLog.is_deleted == False)  # noqa: E712
        return query.first()

    @staticmethod
    def list_stage_worker_logs(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[StageWorkerLog]:
        query = db.query(StageWorkerLog).filter(StageWorkerLog.stage_id == stage_id)
        if not include_deleted:
            query = query.filter(StageWorkerLog.is_deleted == False)  # noqa: E712
        return query.order_by(StageWorkerLog.created_at.asc()).all()

    @staticmethod
    def update_worker_payment_status(
        db: Session,
        worker_log: StageWorkerLog,
        payment_status: str,
        updated_by: uuid.UUID,
    ) -> StageWorkerLog:
        worker_log.payment_status = payment_status
        worker_log.updated_by = updated_by
        worker_log.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(worker_log)
        return worker_log

    @staticmethod
    def soft_delete_worker_log(
        db: Session,
        worker_log: StageWorkerLog,
        deleted_by: uuid.UUID,
    ) -> StageWorkerLog:
        worker_log.is_deleted = True
        worker_log.deleted_at = datetime.now(timezone.utc)
        worker_log.deleted_by = deleted_by
        worker_log.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(worker_log)
        return worker_log

    # ==========================================
    # Stage Expense Data Access
    # ==========================================

    @staticmethod
    def add_expense(
        db: Session,
        stage: CultivationStage,
        expense_data: dict,
        created_by: uuid.UUID,
    ) -> StageExpense:
        expense = StageExpense(
            id=uuid.uuid4(),
            stage_id=stage.id,
            cultivation_id=stage.cultivation_id,
            expense_category=expense_data["expense_category"],
            title=expense_data["title"],
            amount=expense_data["amount"],
            payment_mode=expense_data.get("payment_mode", "CASH"),
            worker_count=expense_data.get("worker_count"),
            per_head_wage=expense_data.get("per_head_wage"),
            quantity_desc=expense_data.get("quantity_desc"),
            machinery_type=expense_data.get("machinery_type"),
            bill_image_url=expense_data.get("bill_image_url"),
            notes=expense_data.get("notes"),
            created_by=created_by,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def get_expense_by_id(
        db: Session,
        expense_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[StageExpense]:
        query = (
            db.query(StageExpense)
            .options(joinedload(StageExpense.cultivation))
            .filter(StageExpense.id == expense_id)
        )
        if not include_deleted:
            query = query.filter(StageExpense.is_deleted == False)  # noqa: E712
        return query.first()

    @staticmethod
    def list_stage_expenses(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[StageExpense]:
        query = db.query(StageExpense).filter(StageExpense.stage_id == stage_id)
        if not include_deleted:
            query = query.filter(StageExpense.is_deleted == False)  # noqa: E712
        return query.order_by(StageExpense.created_at.desc()).all()

    @staticmethod
    def soft_delete_expense(
        db: Session,
        expense: StageExpense,
        deleted_by: uuid.UUID,
    ) -> StageExpense:
        expense.is_deleted = True
        expense.deleted_at = datetime.now(timezone.utc)
        expense.deleted_by = deleted_by
        expense.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def restore_expense(
        db: Session,
        expense: StageExpense,
        updated_by: uuid.UUID,
    ) -> StageExpense:
        expense.is_deleted = False
        expense.deleted_at = None
        expense.deleted_by = None
        expense.updated_by = updated_by
        expense.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(expense)
        return expense

    # ==========================================
    # Harvest Metrics & Yield Data Access
    # ==========================================

    @staticmethod
    def update_harvest_metrics(
        db: Session,
        run: CultivationRun,
        yield_quantity: Decimal,
        selling_price_per_unit: Decimal,
        yield_unit: Optional[str] = "Bags / மூட்டை",
        gross_revenue: Optional[Decimal] = None,
        updated_by: uuid.UUID = None,
    ) -> CultivationRun:
        run.yield_quantity = yield_quantity
        run.selling_price_per_unit = selling_price_per_unit
        run.yield_unit = yield_unit or "Bags / மூட்டை"
        run.gross_revenue = gross_revenue if gross_revenue is not None else (yield_quantity * selling_price_per_unit)
        run.updated_by = updated_by
        run.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run

