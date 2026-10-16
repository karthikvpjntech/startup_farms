import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc

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
from app.models.cultivation import CultivationRun, CultivationStage, StageExpense
from app.models.farm import Farm
from app.models.crop import Crop
from app.models.supplier import Supplier
from app.models.enums import StageStatus, BillStatus, PaymentStatus


class FarmerCRMRepository:
    """Repository handling all database persistence and complex aggregations for Farmer CRM / Farm Operations."""

    # ==========================================
    # Worker Master Persistence
    # ==========================================

    @staticmethod
    def create_worker(
        db: Session,
        farmer_profile_id: uuid.UUID,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> Worker:
        worker_code = data.get("worker_code")
        if not worker_code:
            # Generate deterministic/sequential code WKR-XXXX
            count = db.scalar(
                select(func.count(Worker.id)).where(Worker.farmer_profile_id == farmer_profile_id)
            ) or 0
            worker_code = f"WKR-{count + 1001}"

        worker = Worker(
            id=uuid.uuid4(),
            farmer_profile_id=farmer_profile_id,
            worker_code=worker_code,
            full_name=data["full_name"],
            mobile_number=data["mobile_number"],
            gender=data.get("gender", "MALE"),
            skill=data.get("skill", "GENERAL_LABOR"),
            daily_salary=Decimal(str(data.get("daily_salary", "0.00"))),
            village=data.get("village"),
            address=data.get("address"),
            payment_preference=data.get("payment_preference", "CASH"),
            user_id=data.get("user_id"),
            is_active=data.get("is_active", True),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)
        return worker

    @staticmethod
    def get_worker_by_id(
        db: Session,
        worker_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False,
    ) -> Optional[Worker]:
        query = select(Worker).where(Worker.id == worker_id)
        if farmer_profile_id:
            query = query.where(Worker.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            query = query.where(Worker.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def get_worker_by_mobile(
        db: Session,
        farmer_profile_id: uuid.UUID,
        mobile_number: str,
    ) -> Optional[Worker]:
        return db.scalar(
            select(Worker).where(
                and_(
                    Worker.farmer_profile_id == farmer_profile_id,
                    Worker.mobile_number == mobile_number,
                    Worker.is_deleted == False,
                )
            )
        )

    @staticmethod
    def list_workers(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        skill: Optional[str] = None,
        gender: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Worker]:
        query = select(Worker).where(
            and_(
                Worker.farmer_profile_id == farmer_profile_id,
                Worker.is_deleted == False,
            )
        )
        if is_active is not None:
            query = query.where(Worker.is_active == is_active)
        if skill:
            query = query.where(Worker.skill == skill)
        if gender:
            query = query.where(Worker.gender == gender)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Worker.full_name.ilike(search_term),
                    Worker.mobile_number.ilike(search_term),
                    Worker.worker_code.ilike(search_term),
                    Worker.village.ilike(search_term),
                    Worker.skill.ilike(search_term),
                )
            )
        query = query.order_by(Worker.full_name.asc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_workers(
        db: Session,
        farmer_profile_id: uuid.UUID,
        search: Optional[str] = None,
        skill: Optional[str] = None,
        gender: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        query = select(func.count(Worker.id)).where(
            and_(
                Worker.farmer_profile_id == farmer_profile_id,
                Worker.is_deleted == False,
            )
        )
        if is_active is not None:
            query = query.where(Worker.is_active == is_active)
        if skill:
            query = query.where(Worker.skill == skill)
        if gender:
            query = query.where(Worker.gender == gender)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Worker.full_name.ilike(search_term),
                    Worker.mobile_number.ilike(search_term),
                    Worker.worker_code.ilike(search_term),
                    Worker.village.ilike(search_term),
                    Worker.skill.ilike(search_term),
                )
            )
        return db.scalar(query) or 0

    @staticmethod
    def update_worker(
        db: Session,
        worker: Worker,
        data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None,
    ) -> Worker:
        for key, val in data.items():
            if val is not None and hasattr(worker, key):
                if key == "daily_salary":
                    setattr(worker, key, Decimal(str(val)))
                else:
                    setattr(worker, key, val)
        worker.updated_by = updated_by
        worker.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(worker)
        return worker

    @staticmethod
    def soft_delete_worker(
        db: Session,
        worker: Worker,
        deleted_by: Optional[uuid.UUID] = None,
    ) -> Worker:
        worker.is_deleted = True
        worker.is_active = False
        worker.deleted_at = datetime.now(timezone.utc)
        worker.deleted_by = deleted_by
        db.commit()
        db.refresh(worker)
        return worker

    # ==========================================
    # Machine Master Persistence
    # ==========================================

    @staticmethod
    def create_machine(
        db: Session,
        farmer_profile_id: uuid.UUID,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> Machine:
        machine_code = data.get("machine_code")
        if not machine_code:
            count = db.scalar(
                select(func.count(Machine.id)).where(Machine.farmer_profile_id == farmer_profile_id)
            ) or 0
            machine_code = f"MCH-{count + 1001}"

        machine = Machine(
            id=uuid.uuid4(),
            farmer_profile_id=farmer_profile_id,
            machine_code=machine_code,
            machine_name=data["machine_name"],
            machine_type=data.get("machine_type", "TRACTOR"),
            ownership_type=data.get("ownership_type", "OWNED"),
            owner_name=data.get("owner_name"),
            owner_contact=data.get("owner_contact"),
            rate_per_hour=Decimal(str(data["rate_per_hour"])) if data.get("rate_per_hour") is not None else None,
            rate_per_day=Decimal(str(data["rate_per_day"])) if data.get("rate_per_day") is not None else None,
            operator_included=data.get("operator_included", False),
            is_active=data.get("is_active", True),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(machine)
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def get_machine_by_id(
        db: Session,
        machine_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False,
    ) -> Optional[Machine]:
        query = select(Machine).where(Machine.id == machine_id)
        if farmer_profile_id:
            query = query.where(Machine.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            query = query.where(Machine.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def list_machines(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        machine_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Machine]:
        query = select(Machine).where(
            and_(
                Machine.farmer_profile_id == farmer_profile_id,
                Machine.is_deleted == False,
            )
        )
        if is_active is not None:
            query = query.where(Machine.is_active == is_active)
        if machine_type:
            query = query.where(Machine.machine_type == machine_type)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Machine.machine_name.ilike(search_term),
                    Machine.machine_code.ilike(search_term),
                    Machine.machine_type.ilike(search_term),
                )
            )
        query = query.order_by(Machine.machine_name.asc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_machines(
        db: Session,
        farmer_profile_id: uuid.UUID,
        search: Optional[str] = None,
        machine_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        query = select(func.count(Machine.id)).where(
            and_(
                Machine.farmer_profile_id == farmer_profile_id,
                Machine.is_deleted == False,
            )
        )
        if is_active is not None:
            query = query.where(Machine.is_active == is_active)
        if machine_type:
            query = query.where(Machine.machine_type == machine_type)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Machine.machine_name.ilike(search_term),
                    Machine.machine_code.ilike(search_term),
                    Machine.machine_type.ilike(search_term),
                )
            )
        return db.scalar(query) or 0

    @staticmethod
    def update_machine(
        db: Session,
        machine: Machine,
        data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None,
    ) -> Machine:
        for key, val in data.items():
            if val is not None and hasattr(machine, key):
                if key in ("rate_per_hour", "rate_per_day"):
                    setattr(machine, key, Decimal(str(val)))
                else:
                    setattr(machine, key, val)
        machine.updated_by = updated_by
        machine.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(machine)
        return machine

    @staticmethod
    def soft_delete_machine(
        db: Session,
        machine: Machine,
        deleted_by: Optional[uuid.UUID] = None,
    ) -> Machine:
        machine.is_deleted = True
        machine.is_active = False
        machine.deleted_at = datetime.now(timezone.utc)
        machine.deleted_by = deleted_by
        db.commit()
        db.refresh(machine)
        return machine

    # ==========================================
    # Worker Attendance Persistence
    # ==========================================

    @staticmethod
    def add_attendance(
        db: Session,
        stage: CultivationStage,
        worker: Worker,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> WorkerAttendance:
        working_days = Decimal(str(data.get("working_days", "1.00")))
        daily_salary = Decimal(str(data.get("daily_salary") or worker.daily_salary))
        overtime_amount = Decimal(str(data.get("overtime_amount", "0.00")))
        calculated_amount = (working_days * daily_salary) + overtime_amount

        attendance = WorkerAttendance(
            id=uuid.uuid4(),
            stage_id=stage.id,
            cultivation_id=stage.cultivation_id,
            worker_id=worker.id,
            work_date=data.get("work_date") or date.today(),
            start_time=data.get("start_time", "08:00 AM"),
            end_time=data.get("end_time", "05:00 PM"),
            break_hours=Decimal(str(data.get("break_hours", "1.00"))),
            total_hours=Decimal(str(data.get("total_hours", "8.00"))),
            working_days=working_days,
            daily_salary=daily_salary,
            overtime_amount=overtime_amount,
            calculated_amount=calculated_amount,
            payment_status="PENDING",
            notes=data.get("notes"),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def list_attendances_by_stage(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[WorkerAttendance]:
        query = select(WorkerAttendance).where(WorkerAttendance.stage_id == stage_id)
        if not include_deleted:
            query = query.where(WorkerAttendance.is_deleted == False)
        query = query.order_by(WorkerAttendance.work_date.asc(), WorkerAttendance.created_at.asc())
        return list(db.scalars(query).all())

    @staticmethod
    def get_attendance_by_id(
        db: Session,
        attendance_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[WorkerAttendance]:
        query = select(WorkerAttendance).where(WorkerAttendance.id == attendance_id)
        if not include_deleted:
            query = query.where(WorkerAttendance.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def soft_delete_attendance(
        db: Session,
        attendance: WorkerAttendance,
        deleted_by: Optional[uuid.UUID] = None,
    ) -> WorkerAttendance:
        attendance.is_deleted = True
        attendance.deleted_at = datetime.now(timezone.utc)
        attendance.deleted_by = deleted_by
        db.commit()
        db.refresh(attendance)
        return attendance

    # ==========================================
    # Machine Usage Persistence
    # ==========================================

    @staticmethod
    def add_machine_usage(
        db: Session,
        stage: CultivationStage,
        machine: Machine,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> MachineUsage:
        hours_used = Decimal(str(data.get("hours_used", "0.00")))
        days_used = Decimal(str(data.get("days_used", "0.00")))
        
        # Calculate rate applied
        rate_applied = Decimal(str(data.get("rate_applied") or (machine.rate_per_hour if hours_used > 0 else machine.rate_per_day) or "0.00"))
        fuel_cost = Decimal(str(data.get("fuel_cost", "0.00")))
        operator_cost = Decimal(str(data.get("operator_cost", "0.00")))
        
        if hours_used > 0:
            usage_cost = hours_used * rate_applied
        else:
            usage_cost = days_used * rate_applied
        total_cost = usage_cost + fuel_cost + operator_cost

        usage = MachineUsage(
            id=uuid.uuid4(),
            stage_id=stage.id,
            cultivation_id=stage.cultivation_id,
            machine_id=machine.id,
            usage_date=data.get("usage_date") or date.today(),
            hours_used=hours_used,
            days_used=days_used,
            rate_applied=rate_applied,
            fuel_cost=fuel_cost,
            operator_cost=operator_cost,
            total_cost=total_cost,
            notes=data.get("notes"),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
        return usage

    @staticmethod
    def list_machine_usages_by_stage(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> List[MachineUsage]:
        query = select(MachineUsage).where(MachineUsage.stage_id == stage_id)
        if not include_deleted:
            query = query.where(MachineUsage.is_deleted == False)
        query = query.order_by(MachineUsage.usage_date.asc(), MachineUsage.created_at.asc())
        return list(db.scalars(query).all())

    @staticmethod
    def get_machine_usage_by_id(
        db: Session,
        usage_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[MachineUsage]:
        query = select(MachineUsage).where(MachineUsage.id == usage_id)
        if not include_deleted:
            query = query.where(MachineUsage.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def soft_delete_machine_usage(
        db: Session,
        usage: MachineUsage,
        deleted_by: Optional[uuid.UUID] = None,
    ) -> MachineUsage:
        usage.is_deleted = True
        usage.deleted_at = datetime.now(timezone.utc)
        usage.deleted_by = deleted_by
        db.commit()
        db.refresh(usage)
        return usage

    # ==========================================
    # Material Purchases Persistence
    # ==========================================

    @staticmethod
    def create_material_purchase(
        db: Session,
        farmer_profile_id: uuid.UUID,
        supplier: Supplier,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> MaterialPurchase:
        count = db.scalar(
            select(func.count(MaterialPurchase.id)).where(MaterialPurchase.farmer_profile_id == farmer_profile_id)
        ) or 0
        purchase_code = f"PUR-{count + 1001}"

        qty = Decimal(str(data["quantity"]))
        unit_rate = Decimal(str(data["unit_rate"]))
        subtotal = qty * unit_rate
        tax_amount = Decimal(str(data.get("tax_amount", "0.00")))
        total_amount = subtotal + tax_amount

        purchase = MaterialPurchase(
            id=uuid.uuid4(),
            purchase_code=purchase_code,
            farmer_profile_id=farmer_profile_id,
            cultivation_id=data.get("cultivation_id"),
            stage_id=data.get("stage_id"),
            supplier_id=supplier.id,
            material_category=data.get("material_category", "SEED"),
            material_name=data["material_name"],
            quantity=qty,
            unit=data.get("unit", "KG"),
            unit_rate=unit_rate,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            purchase_date=data.get("purchase_date") or date.today(),
            payment_status="PENDING",
            notes=data.get("notes"),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        return purchase

    @staticmethod
    def list_purchases(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
        stage_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MaterialPurchase]:
        query = select(MaterialPurchase).where(
            and_(
                MaterialPurchase.farmer_profile_id == farmer_profile_id,
                MaterialPurchase.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(MaterialPurchase.cultivation_id == cultivation_id)
        if stage_id:
            query = query.where(MaterialPurchase.stage_id == stage_id)
        query = query.order_by(MaterialPurchase.purchase_date.desc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_purchases(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
    ) -> int:
        query = select(func.count(MaterialPurchase.id)).where(
            and_(
                MaterialPurchase.farmer_profile_id == farmer_profile_id,
                MaterialPurchase.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(MaterialPurchase.cultivation_id == cultivation_id)
        return db.scalar(query) or 0

    @staticmethod
    def get_purchase_by_id(
        db: Session,
        purchase_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[MaterialPurchase]:
        query = select(MaterialPurchase).where(MaterialPurchase.id == purchase_id)
        if not include_deleted:
            query = query.where(MaterialPurchase.is_deleted == False)
        return db.scalar(query)

    # ==========================================
    # Cultivation Schedules Persistence
    # ==========================================

    @staticmethod
    def create_or_update_schedules(
        db: Session,
        cultivation_id: uuid.UUID,
        schedules_data: List[Dict[str, Any]],
        created_by: Optional[uuid.UUID] = None,
    ) -> List[CultivationSchedule]:
        # Delete existing schedules for this run if any
        existing = db.scalars(
            select(CultivationSchedule).where(CultivationSchedule.cultivation_id == cultivation_id)
        ).all()
        for e in existing:
            db.delete(e)

        results = []
        for item in schedules_data:
            sch = CultivationSchedule(
                id=uuid.uuid4(),
                cultivation_id=cultivation_id,
                stage_order=item["stage_order"],
                stage_name=item["stage_name"],
                planned_start_date=item["planned_start_date"],
                planned_end_date=item["planned_end_date"],
                estimated_cost=Decimal(str(item.get("estimated_cost", "0.00"))),
                status=item.get("status", "PLANNED"),
                created_by=created_by,
                updated_by=created_by,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(sch)
            results.append(sch)

        db.commit()
        for r in results:
            db.refresh(r)
        return results

    @staticmethod
    def get_schedules(
        db: Session,
        cultivation_id: uuid.UUID,
    ) -> List[CultivationSchedule]:
        return list(
            db.scalars(
                select(CultivationSchedule)
                .where(
                    and_(
                        CultivationSchedule.cultivation_id == cultivation_id,
                        CultivationSchedule.is_deleted == False,
                    )
                )
                .order_by(CultivationSchedule.stage_order.asc())
            ).all()
        )

    # ==========================================
    # Billing & Payments Persistence
    # ==========================================

    @staticmethod
    def create_bill(
        db: Session,
        farmer_profile_id: uuid.UUID,
        farm_id: uuid.UUID,
        bill_type: str,
        recipient_name: str,
        recipient_type: str,
        items_data: List[Dict[str, Any]],
        cultivation_id: Optional[uuid.UUID] = None,
        stage_id: Optional[uuid.UUID] = None,
        recipient_worker_id: Optional[uuid.UUID] = None,
        recipient_supplier_id: Optional[uuid.UUID] = None,
        bill_date: Optional[date] = None,
        due_date: Optional[date] = None,
        tax_amount: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Bill:
        count = db.scalar(
            select(func.count(Bill.id)).where(Bill.farmer_profile_id == farmer_profile_id)
        ) or 0
        year = date.today().year
        bill_number = f"BILL-{year}-{count + 1001}"

        subtotal = Decimal("0.00")
        bill_items = []
        for itm in items_data:
            qty = Decimal(str(itm.get("quantity", "1.00")))
            price = Decimal(str(itm["unit_price"]))
            tot = Decimal(str(itm.get("total_price", qty * price)))
            subtotal += tot
            b_item = BillItem(
                id=uuid.uuid4(),
                item_type=itm.get("item_type", "LABOR"),
                item_description=itm["item_description"],
                quantity=qty,
                unit=itm.get("unit", "UNIT"),
                unit_price=price,
                total_price=tot,
            )
            bill_items.append(b_item)

        total_amount = subtotal + tax_amount - discount_amount

        bill = Bill(
            id=uuid.uuid4(),
            bill_number=bill_number,
            farmer_profile_id=farmer_profile_id,
            farm_id=farm_id,
            cultivation_id=cultivation_id,
            stage_id=stage_id,
            bill_type=bill_type,
            recipient_name=recipient_name,
            recipient_type=recipient_type,
            recipient_worker_id=recipient_worker_id,
            recipient_supplier_id=recipient_supplier_id,
            bill_date=bill_date or date.today(),
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            paid_amount=Decimal("0.00"),
            pending_amount=total_amount,
            status=BillStatus.PENDING.value,
            notes=notes,
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        bill.items = bill_items
        db.add(bill)
        db.commit()
        db.refresh(bill)
        return bill

    @staticmethod
    def get_bill_by_id(
        db: Session,
        bill_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False,
    ) -> Optional[Bill]:
        query = select(Bill).where(Bill.id == bill_id)
        if farmer_profile_id:
            query = query.where(Bill.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            query = query.where(Bill.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def list_bills(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
        stage_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        bill_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Bill]:
        query = select(Bill).where(
            and_(
                Bill.farmer_profile_id == farmer_profile_id,
                Bill.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(Bill.cultivation_id == cultivation_id)
        if stage_id:
            query = query.where(Bill.stage_id == stage_id)
        if status:
            query = query.where(Bill.status == status)
        if bill_type:
            query = query.where(Bill.bill_type == bill_type)
        query = query.order_by(Bill.bill_date.desc(), Bill.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_bills(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        query = select(func.count(Bill.id)).where(
            and_(
                Bill.farmer_profile_id == farmer_profile_id,
                Bill.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(Bill.cultivation_id == cultivation_id)
        if status:
            query = query.where(Bill.status == status)
        return db.scalar(query) or 0

    @staticmethod
    def create_payment(
        db: Session,
        bill: Bill,
        amount: Decimal,
        payment_method: str,
        transaction_reference: Optional[str] = None,
        payment_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Payment:
        count = db.scalar(
            select(func.count(Payment.id)).where(Payment.farmer_profile_id == bill.farmer_profile_id)
        ) or 0
        year = date.today().year
        payment_number = f"PAY-{year}-{count + 1001}"

        payment = Payment(
            id=uuid.uuid4(),
            payment_number=payment_number,
            bill_id=bill.id,
            farmer_profile_id=bill.farmer_profile_id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date or datetime.now(timezone.utc),
            status=PaymentStatus.PAID.value,
            transaction_reference=transaction_reference,
            notes=notes,
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(payment)

        # Update bill settlement totals
        bill.paid_amount += amount
        bill.pending_amount = max(Decimal("0.00"), bill.total_amount - bill.paid_amount)
        if bill.pending_amount <= Decimal("0.00"):
            bill.status = BillStatus.PAID.value
        else:
            bill.status = BillStatus.PARTIALLY_PAID.value
        bill.updated_at = datetime.now(timezone.utc)
        bill.updated_by = created_by

        # If bill is linked to worker attendances, update them
        attendances = db.scalars(
            select(WorkerAttendance).where(WorkerAttendance.bill_id == bill.id)
        ).all()
        for att in attendances:
            if bill.status == BillStatus.PAID.value:
                att.payment_status = "PAID"
                att.updated_at = datetime.now(timezone.utc)

        # If bill is linked to material purchases, update them
        purchases = db.scalars(
            select(MaterialPurchase).where(MaterialPurchase.bill_id == bill.id)
        ).all()
        for pur in purchases:
            pur.payment_status = bill.status
            pur.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(payment)
        db.refresh(bill)
        return payment

    @staticmethod
    def list_payments(
        db: Session,
        farmer_profile_id: uuid.UUID,
        bill_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        query = select(Payment).where(
            and_(
                Payment.farmer_profile_id == farmer_profile_id,
                Payment.is_deleted == False,
            )
        )
        if bill_id:
            query = query.where(Payment.bill_id == bill_id)
        query = query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_payments(
        db: Session,
        farmer_profile_id: uuid.UUID,
        bill_id: Optional[uuid.UUID] = None,
    ) -> int:
        query = select(func.count(Payment.id)).where(
            and_(
                Payment.farmer_profile_id == farmer_profile_id,
                Payment.is_deleted == False,
            )
        )
        if bill_id:
            query = query.where(Payment.bill_id == bill_id)
        return db.scalar(query) or 0

    # ==========================================
    # Logistics Persistence
    # ==========================================

    @staticmethod
    def create_logistics(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: uuid.UUID,
        farm_id: uuid.UUID,
        data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> Logistics:
        count = db.scalar(
            select(func.count(Logistics.id)).where(Logistics.farmer_profile_id == farmer_profile_id)
        ) or 0
        dispatch_code = f"LOG-{count + 1001}"

        trans_cost = Decimal(str(data.get("transport_cost", "0.00")))
        load_cost = Decimal(str(data.get("loading_cost", "0.00")))
        unload_cost = Decimal(str(data.get("unloading_cost", "0.00")))
        total_cost = trans_cost + load_cost + unload_cost

        logistics = Logistics(
            id=uuid.uuid4(),
            dispatch_code=dispatch_code,
            farmer_profile_id=farmer_profile_id,
            cultivation_id=cultivation_id,
            farm_id=farm_id,
            harvest_location=data["harvest_location"],
            destination=data["destination"],
            pickup_date=data.get("pickup_date") or datetime.now(timezone.utc),
            delivery_date=data.get("delivery_date"),
            vehicle_number=data["vehicle_number"],
            driver_name=data["driver_name"],
            driver_contact=data["driver_contact"],
            driver_id=data.get("driver_id"),
            quantity_transported=Decimal(str(data["quantity_transported"])),
            quantity_unit=data.get("quantity_unit", "KG"),
            transport_cost=trans_cost,
            loading_cost=load_cost,
            unloading_cost=unload_cost,
            total_logistics_cost=total_cost,
            status=data.get("status", "PLANNED"),
            notes=data.get("notes"),
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(logistics)
        db.commit()
        db.refresh(logistics)
        return logistics

    @staticmethod
    def list_logistics(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Logistics]:
        query = select(Logistics).where(
            and_(
                Logistics.farmer_profile_id == farmer_profile_id,
                Logistics.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(Logistics.cultivation_id == cultivation_id)
        query = query.order_by(Logistics.pickup_date.desc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def count_logistics(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cultivation_id: Optional[uuid.UUID] = None,
    ) -> int:
        query = select(func.count(Logistics.id)).where(
            and_(
                Logistics.farmer_profile_id == farmer_profile_id,
                Logistics.is_deleted == False,
            )
        )
        if cultivation_id:
            query = query.where(Logistics.cultivation_id == cultivation_id)
        return db.scalar(query) or 0

    @staticmethod
    def get_logistics_by_id(
        db: Session,
        logistics_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[Logistics]:
        query = select(Logistics).where(Logistics.id == logistics_id)
        if not include_deleted:
            query = query.where(Logistics.is_deleted == False)
        return db.scalar(query)

    @staticmethod
    def update_logistics_status(
        db: Session,
        logistics: Logistics,
        status_val: str,
        delivery_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        updated_by: Optional[uuid.UUID] = None,
    ) -> Logistics:
        logistics.status = status_val
        if delivery_date:
            logistics.delivery_date = delivery_date
        if notes:
            logistics.notes = notes
        logistics.updated_by = updated_by
        logistics.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(logistics)
        return logistics

    # ==========================================
    # SMS Logs Persistence
    # ==========================================

    @staticmethod
    def list_sms_logs(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SMSLog]:
        query = select(SMSLog).where(
            and_(
                SMSLog.farmer_profile_id == farmer_profile_id,
                SMSLog.is_deleted == False,
            )
        ).order_by(SMSLog.created_at.desc(), SMSLog.id.desc()).offset(skip).limit(limit)
        return list(db.scalars(query).all())

    @staticmethod
    def list_sms_logs_cursor(
        db: Session,
        farmer_profile_id: uuid.UUID,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[SMSLog]:
        """
        Keyset cursor query preventing data drift:
        WHERE (created_at < cursor_created_at) OR (created_at == cursor_created_at AND id < cursor_id)
        ORDER BY created_at DESC, id DESC
        LIMIT limit + 1
        """
        conditions = [
            SMSLog.farmer_profile_id == farmer_profile_id,
            SMSLog.is_deleted == False,
        ]
        if cursor_created_at and cursor_id:
            conditions.append(
                or_(
                    SMSLog.created_at < cursor_created_at,
                    and_(
                        SMSLog.created_at == cursor_created_at,
                        SMSLog.id < cursor_id,
                    ),
                )
            )
        elif cursor_created_at:
            conditions.append(SMSLog.created_at < cursor_created_at)

        query = (
            select(SMSLog)
            .where(and_(*conditions))
            .order_by(SMSLog.created_at.desc(), SMSLog.id.desc())
            .limit(limit + 1)
        )
        return list(db.scalars(query).all())

    @staticmethod
    def count_sms_logs(
        db: Session,
        farmer_profile_id: uuid.UUID,
    ) -> int:
        return db.scalar(
            select(func.count(SMSLog.id)).where(
                and_(
                    SMSLog.farmer_profile_id == farmer_profile_id,
                    SMSLog.is_deleted == False,
                )
            )
        ) or 0
