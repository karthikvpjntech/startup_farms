import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Date,
    Integer,
    Numeric,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import StageStatus, ExpenseCategory, PaymentMode, MachineryOwnership


DEFAULT_CULTIVATION_STAGES = [
    (1, "Land Preparation & Tillage / நில உழவு"),
    (2, "Sowing & Planting / நடவு பணி"),
    (3, "Weeding / களை எடுத்தல்"),
    (4, "Fertilization & Spraying / உரம் & மருந்து"),
    (5, "Maturation & Pre-Harvest / அறுவடைக்கு முந்தைய நிலை"),
]


class CultivationRun(Base):
    """Represents an active or archived cultivation cycle instantiated from a FarmCropPlan."""
    __tablename__ = "cultivation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_crop_plan_id = Column(UUID(as_uuid=True), ForeignKey("farm_crop_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_profile_id = Column(UUID(as_uuid=True), ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sowing_date = Column(Date, nullable=False)
    maturity_days = Column(Integer, nullable=False, default=90)
    target_harvest_date = Column(Date, nullable=False)
    current_stage_order = Column(Integer, nullable=False, default=1)

    # Farming methodology & Multi-Season Comparison Metrics
    farming_method = Column(String(50), nullable=False, default="CONVENTIONAL")  # CONVENTIONAL vs ORGANIC vs NATURAL
    season_year = Column(String(50), nullable=True)  # e.g., '2025 Kharif', '2026 Rabi'
    land_area = Column(Numeric(8, 2), nullable=True)  # Land area in acres/hectares
    land_area_unit = Column(String(20), nullable=False, default="ACRE")
    yield_quantity = Column(Numeric(10, 2), nullable=True)  # e.g., 100 bags or 5000 kg
    yield_unit = Column(String(50), nullable=True, default="Bags / மூட்டை")
    selling_price_per_unit = Column(Numeric(10, 2), nullable=True)  # e.g., ₹2700 / bag
    gross_revenue = Column(Numeric(12, 2), nullable=True)  # e.g., ₹2,70,000

    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    farm_crop_plan = relationship("FarmCropPlan", backref="cultivation_runs", lazy="joined")
    farmer_profile = relationship("FarmerProfile", backref="cultivation_runs", lazy="joined")
    stages = relationship("CultivationStage", back_populates="cultivation", cascade="all, delete-orphan", order_by="CultivationStage.stage_order")
    expenses = relationship("StageExpense", back_populates="cultivation", cascade="all, delete-orphan")
    worker_logs = relationship("StageWorkerLog", back_populates="cultivation", cascade="all, delete-orphan")
    pre_activity_plans = relationship("PreActivityPlan", back_populates="cultivation", cascade="all, delete-orphan")


class CultivationStage(Base):
    """Represents a sequential stage in a cultivation run lifecycle."""
    __tablename__ = "cultivation_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultivation_id = Column(UUID(as_uuid=True), ForeignKey("cultivation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    stage_order = Column(Integer, nullable=False)
    stage_name = Column(String(200), nullable=False)
    farming_type = Column(String(50), nullable=False, default="CONVENTIONAL")  # CONVENTIONAL vs ORGANIC
    status = Column(String(50), nullable=False, default=StageStatus.PENDING.value)
    
    start_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    image_url = Column(String(500), nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    cultivation = relationship("CultivationRun", back_populates="stages")
    expenses = relationship("StageExpense", back_populates="stage", cascade="all, delete-orphan", order_by="desc(StageExpense.created_at)")
    worker_logs = relationship("StageWorkerLog", back_populates="stage", cascade="all, delete-orphan", order_by="StageWorkerLog.created_at")
    pre_activity_plans = relationship("PreActivityPlan", back_populates="stage", cascade="all, delete-orphan", order_by="PreActivityPlan.created_at")


class StageWorkerLog(Base):
    """Represents individual worker daily attendance, wage log and settlement status."""
    __tablename__ = "stage_worker_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("cultivation_stages.id", ondelete="CASCADE"), nullable=False, index=True)
    cultivation_id = Column(UUID(as_uuid=True), ForeignKey("cultivation_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    worker_name = Column(String(150), nullable=False)  # e.g. 'மாரியம்மாள்', 'கந்தசாமி'
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    days_worked = Column(Numeric(6, 1), nullable=False)  # e.g. 4.0 or 2.5 days
    daily_wage = Column(Numeric(10, 2), nullable=False)  # e.g. ₹350
    total_wage = Column(Numeric(12, 2), nullable=False)  # days_worked * daily_wage = ₹1400
    payment_status = Column(String(30), nullable=False, default="PENDING")  # PAID vs PENDING
    notes = Column(Text, nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    stage = relationship("CultivationStage", back_populates="worker_logs")
    cultivation = relationship("CultivationRun", back_populates="worker_logs")
    worker_user = relationship("User", foreign_keys=[worker_id], lazy="joined")


class StageExpense(Base):
    """Represents an itemized field expense logged under a cultivation stage."""
    __tablename__ = "stage_expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("cultivation_stages.id", ondelete="CASCADE"), nullable=False, index=True)
    cultivation_id = Column(UUID(as_uuid=True), ForeignKey("cultivation_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    expense_category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(50), nullable=False, default=PaymentMode.CASH.value)

    worker_count = Column(Integer, nullable=True)
    per_head_wage = Column(Numeric(10, 2), nullable=True)
    quantity_desc = Column(String(200), nullable=True)
    machinery_type = Column(String(50), nullable=True)
    bill_image_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    stage = relationship("CultivationStage", back_populates="expenses")
    cultivation = relationship("CultivationRun", back_populates="expenses")


# Alias for backward compatibility
StageExpenseLog = StageExpense


