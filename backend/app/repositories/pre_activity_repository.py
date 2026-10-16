import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.pre_activity_plan import PreActivityPlan
from app.models.cultivation import CultivationStage, CultivationRun, StageExpense, StageWorkerLog
from app.models.enums import ExpenseCategory, PaymentMode, WorkerPaymentStatus
from app.schemas.pre_activity_plan import PreActivityPlanCreate, PreActivityPlanUpdate, PreActivityConvertRequest


class PreActivityRepository:
    """Repository handling CRUD operations and automated 1-click ledger conversions for Pre-Activity Plans."""

    @staticmethod
    def create_plan(
        db: Session,
        stage: CultivationStage,
        data: PreActivityPlanCreate,
        created_by: uuid.UUID,
    ) -> PreActivityPlan:
        # Calculate estimated total cost from machinery, materials, and labor if not explicitly provided
        machinery_cost = Decimal(str(data.machinery_details.get("total_machinery_cost", 0))) if data.machinery_details else Decimal("0.00")
        
        material_cost = Decimal("0.00")
        if data.materials_details:
            for item in data.materials_details:
                cost = Decimal(str(item.get("total_cost", 0)))
                material_cost += cost

        labor_cost = Decimal(str(data.labor_details.get("total_labor_cost", 0))) if data.labor_details else Decimal("0.00")
        computed_total = machinery_cost + material_cost + labor_cost

        total_cost = data.estimated_total_cost if data.estimated_total_cost > 0 else computed_total

        plan = PreActivityPlan(
            id=uuid.uuid4(),
            stage_id=stage.id,
            cultivation_id=stage.cultivation_id,
            activity_name=data.activity_name,
            activity_type=data.activity_type or "TILLAGE",
            purpose=data.purpose,
            machinery_mode=data.machinery_mode or "NONE",
            machinery_details=data.machinery_details or {},
            materials_details=data.materials_details or [],
            labor_details=data.labor_details or {},
            estimated_total_cost=total_cost,
            status=data.status or "PLANNED",
            actual_converted=False,
            is_deleted=False,
            created_by=created_by,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def get_by_id(
        db: Session,
        plan_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[PreActivityPlan]:
        query = db.query(PreActivityPlan).filter(PreActivityPlan.id == plan_id)
        if not include_deleted:
            query = query.filter(PreActivityPlan.is_deleted == False)  # noqa: E712
        return query.first()

    @staticmethod
    def list_by_stage(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[PreActivityPlan]:
        query = (
            db.query(PreActivityPlan)
            .filter(PreActivityPlan.stage_id == stage_id)
            .order_by(PreActivityPlan.created_at.asc())
        )
        if not include_deleted:
            query = query.filter(PreActivityPlan.is_deleted == False)  # noqa: E712
        return query.all()

    @staticmethod
    def list_by_cultivation(
        db: Session,
        cultivation_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[PreActivityPlan]:
        query = (
            db.query(PreActivityPlan)
            .filter(PreActivityPlan.cultivation_id == cultivation_id)
            .order_by(PreActivityPlan.created_at.asc())
        )
        if not include_deleted:
            query = query.filter(PreActivityPlan.is_deleted == False)  # noqa: E712
        return query.all()

    @staticmethod
    def update_plan(
        db: Session,
        plan: PreActivityPlan,
        data: PreActivityPlanUpdate,
        updated_by: uuid.UUID,
    ) -> PreActivityPlan:
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(plan, key, value)

        plan.updated_by = updated_by
        plan.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def delete_plan(
        db: Session,
        plan: PreActivityPlan,
        deleted_by: uuid.UUID,
    ) -> PreActivityPlan:
        plan.is_deleted = True
        plan.deleted_at = datetime.now(timezone.utc)
        plan.deleted_by = deleted_by
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def convert_to_actual_ledger(
        db: Session,
        plan: PreActivityPlan,
        request: PreActivityConvertRequest,
        user_id: uuid.UUID,
    ) -> Tuple[int, int, Decimal]:
        """
        Converts the pre-activity plan requirements into actual StageExpense and StageWorkerLog records.
        Returns (expenses_count, workers_count, total_amount).
        """
        expenses_created = 0
        workers_created = 0
        total_logged = Decimal("0.00")
        payment_mode_val = request.payment_mode or PaymentMode.CASH.value

        # 1. Convert Machinery Requirements to StageExpense
        machinery_details = plan.machinery_details or {}
        machinery_cost = Decimal(str(machinery_details.get("total_machinery_cost", 0)))
        if machinery_cost > 0:
            m_type = machinery_details.get("machinery_type", "Tractor")
            rental_hrs = machinery_details.get("rental_hours")
            diesel_l = machinery_details.get("diesel_liters")
            
            desc_parts = [f"Mode: {plan.machinery_mode}"]
            if rental_hrs:
                desc_parts.append(f"{rental_hrs} Hrs")
            if diesel_l:
                desc_parts.append(f"{diesel_l} Liters Diesel")

            machinery_expense = StageExpense(
                id=uuid.uuid4(),
                stage_id=plan.stage_id,
                cultivation_id=plan.cultivation_id,
                expense_category=ExpenseCategory.MACHINERY.value,
                title=f"{plan.activity_name} — {m_type} ({plan.machinery_mode})",
                amount=machinery_cost,
                payment_mode=payment_mode_val,
                quantity_desc=", ".join(desc_parts),
                notes=f"Converted from Pre-Task Plan [{plan.activity_name}] - Purpose: {plan.purpose}",
                created_by=user_id,
            )
            db.add(machinery_expense)
            expenses_created += 1
            total_logged += machinery_cost

        # 2. Convert Materials / Manure Requirements to StageExpense
        materials = plan.materials_details or []
        for mat in materials:
            mat_cost = Decimal(str(mat.get("total_cost", 0)))
            if mat_cost > 0:
                item_name = mat.get("item_name", "Material Input")
                qty = mat.get("quantity", 1)
                unit = mat.get("unit", "")
                
                material_expense = StageExpense(
                    id=uuid.uuid4(),
                    stage_id=plan.stage_id,
                    cultivation_id=plan.cultivation_id,
                    expense_category=ExpenseCategory.INPUT_MATERIAL.value,
                    title=f"{plan.activity_name} — {item_name}",
                    amount=mat_cost,
                    payment_mode=payment_mode_val,
                    quantity_desc=f"{qty} {unit}".strip(),
                    notes=f"Converted from Pre-Task Plan [{plan.activity_name}]",
                    created_by=user_id,
                )
                db.add(material_expense)
                expenses_created += 1
                total_logged += mat_cost

        # 3. Convert Labor Requirements to StageWorkerLog
        labor_details = plan.labor_details or {}
        num_workers = int(labor_details.get("estimated_workers", 0))
        wage_per_head = Decimal(str(labor_details.get("wage_per_head", 0)))
        worker_names_list = request.worker_names or labor_details.get("worker_names") or []

        if num_workers > 0 and wage_per_head > 0:
            if worker_names_list and len(worker_names_list) > 0:
                for w_name in worker_names_list[:num_workers]:
                    w_log = StageWorkerLog(
                        id=uuid.uuid4(),
                        stage_id=plan.stage_id,
                        cultivation_id=plan.cultivation_id,
                        worker_name=w_name.strip(),
                        days_worked=Decimal("1.0"),
                        daily_wage=wage_per_head,
                        total_wage=wage_per_head,
                        payment_status=WorkerPaymentStatus.PAID.value if payment_mode_val != "PENDING" else WorkerPaymentStatus.PENDING.value,
                        notes=f"Pre-Task Activity: {plan.activity_name}",
                        created_by=user_id,
                    )
                    db.add(w_log)
                    workers_created += 1
                    total_logged += wage_per_head
            else:
                # Group worker log
                total_labor_wage = wage_per_head * num_workers
                w_log = StageWorkerLog(
                    id=uuid.uuid4(),
                    stage_id=plan.stage_id,
                    cultivation_id=plan.cultivation_id,
                    worker_name=f"கூலி ஆட்கள் ({num_workers} பேர்) — {plan.activity_name}",
                    days_worked=Decimal(str(num_workers)),
                    daily_wage=wage_per_head,
                    total_wage=total_labor_wage,
                    payment_status=WorkerPaymentStatus.PAID.value,
                    notes=f"Group attendance converted from Pre-Task Plan [{plan.activity_name}]",
                    created_by=user_id,
                )
                db.add(w_log)
                workers_created += 1
                total_logged += total_labor_wage

        # 4. Mark Pre-Activity Plan as converted and completed
        plan.actual_converted = True
        plan.status = "COMPLETED"
        plan.converted_at = datetime.now(timezone.utc)
        plan.updated_by = user_id

        db.commit()
        db.refresh(plan)

        return expenses_created, workers_created, total_logged
