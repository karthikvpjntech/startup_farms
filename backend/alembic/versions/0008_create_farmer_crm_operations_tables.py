"""create farmer crm operations tables

Revision ID: 0008_farmer_crm_operations
Revises: 0007_crop_cultivation_stages
Create Date: 2026-09-17 08:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0008_farmer_crm_operations'
down_revision: Union[str, None] = '0007_crop_cultivation_stages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. workers table (Worker Master)
    op.create_table(
        'workers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('worker_code', sa.String(length=50), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('mobile_number', sa.String(length=20), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False, server_default='MALE'),
        sa.Column('skill', sa.String(length=100), nullable=False, server_default='GENERAL_LABOR'),
        sa.Column('daily_salary', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('village', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('payment_preference', sa.String(length=30), nullable=False, server_default='CASH'),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workers_farmer_profile_id'), 'workers', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_workers_worker_code'), 'workers', ['worker_code'], unique=False)
    op.create_index(op.f('ix_workers_full_name'), 'workers', ['full_name'], unique=False)
    op.create_index(op.f('ix_workers_mobile_number'), 'workers', ['mobile_number'], unique=False)
    op.create_index(op.f('ix_workers_user_id'), 'workers', ['user_id'], unique=False)
    op.create_index(op.f('ix_workers_is_active'), 'workers', ['is_active'], unique=False)
    op.create_index(op.f('ix_workers_is_deleted'), 'workers', ['is_deleted'], unique=False)

    # 2. machines table (Machine Master)
    op.create_table(
        'machines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('machine_code', sa.String(length=50), nullable=False),
        sa.Column('machine_name', sa.String(length=150), nullable=False),
        sa.Column('machine_type', sa.String(length=100), nullable=False, server_default='TRACTOR'),
        sa.Column('ownership_type', sa.String(length=50), nullable=False, server_default='OWNED'),
        sa.Column('owner_name', sa.String(length=150), nullable=True),
        sa.Column('owner_contact', sa.String(length=20), nullable=True),
        sa.Column('rate_per_hour', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('rate_per_day', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('operator_included', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machines_farmer_profile_id'), 'machines', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_machines_machine_code'), 'machines', ['machine_code'], unique=False)
    op.create_index(op.f('ix_machines_machine_name'), 'machines', ['machine_name'], unique=False)
    op.create_index(op.f('ix_machines_is_active'), 'machines', ['is_active'], unique=False)
    op.create_index(op.f('ix_machines_is_deleted'), 'machines', ['is_deleted'], unique=False)

    # 3. cultivation_schedules table
    op.create_table(
        'cultivation_schedules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(length=150), nullable=False),
        sa.Column('planned_start_date', sa.Date(), nullable=False),
        sa.Column('planned_end_date', sa.Date(), nullable=False),
        sa.Column('estimated_cost', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PLANNED'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cultivation_schedules_cultivation_id'), 'cultivation_schedules', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_cultivation_schedules_is_deleted'), 'cultivation_schedules', ['is_deleted'], unique=False)

    # 4. bills table
    op.create_table(
        'bills',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('bill_number', sa.String(length=50), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=True),
        sa.Column('stage_id', sa.Uuid(), nullable=True),
        sa.Column('bill_type', sa.String(length=50), nullable=False, server_default='STAGE_CONSOLIDATED'),
        sa.Column('recipient_name', sa.String(length=150), nullable=False),
        sa.Column('recipient_type', sa.String(length=50), nullable=False, server_default='CONSOLIDATED'),
        sa.Column('recipient_worker_id', sa.Uuid(), nullable=True),
        sa.Column('recipient_supplier_id', sa.Uuid(), nullable=True),
        sa.Column('bill_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('pending_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['cultivation_stages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipient_worker_id'], ['workers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipient_supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bills_bill_number'), 'bills', ['bill_number'], unique=True)
    op.create_index(op.f('ix_bills_farmer_profile_id'), 'bills', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_bills_farm_id'), 'bills', ['farm_id'], unique=False)
    op.create_index(op.f('ix_bills_cultivation_id'), 'bills', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_bills_stage_id'), 'bills', ['stage_id'], unique=False)
    op.create_index(op.f('ix_bills_recipient_worker_id'), 'bills', ['recipient_worker_id'], unique=False)
    op.create_index(op.f('ix_bills_recipient_supplier_id'), 'bills', ['recipient_supplier_id'], unique=False)
    op.create_index(op.f('ix_bills_is_deleted'), 'bills', ['is_deleted'], unique=False)

    # 5. bill_items table
    op.create_table(
        'bill_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('bill_id', sa.Uuid(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False, server_default='LABOR'),
        sa.Column('item_description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.00'),
        sa.Column('unit', sa.String(length=30), nullable=False, server_default='UNIT'),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bill_items_bill_id'), 'bill_items', ['bill_id'], unique=False)

    # 6. payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('bill_id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='CASH'),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PAID'),
        sa.Column('transaction_reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_payment_number'), 'payments', ['payment_number'], unique=True)
    op.create_index(op.f('ix_payments_bill_id'), 'payments', ['bill_id'], unique=False)
    op.create_index(op.f('ix_payments_farmer_profile_id'), 'payments', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_payments_is_deleted'), 'payments', ['is_deleted'], unique=False)

    # 7. worker_attendance table
    op.create_table(
        'worker_attendance',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('stage_id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=False),
        sa.Column('worker_id', sa.Uuid(), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.String(length=20), nullable=True),
        sa.Column('end_time', sa.String(length=20), nullable=True),
        sa.Column('break_hours', sa.Numeric(precision=4, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_hours', sa.Numeric(precision=5, scale=2), nullable=False, server_default='8.00'),
        sa.Column('working_days', sa.Numeric(precision=4, scale=2), nullable=False, server_default='1.00'),
        sa.Column('daily_salary', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('overtime_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('calculated_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('bill_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['stage_id'], ['cultivation_stages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worker_attendance_stage_id'), 'worker_attendance', ['stage_id'], unique=False)
    op.create_index(op.f('ix_worker_attendance_cultivation_id'), 'worker_attendance', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_worker_attendance_worker_id'), 'worker_attendance', ['worker_id'], unique=False)
    op.create_index(op.f('ix_worker_attendance_bill_id'), 'worker_attendance', ['bill_id'], unique=False)
    op.create_index(op.f('ix_worker_attendance_is_deleted'), 'worker_attendance', ['is_deleted'], unique=False)

    # 8. machine_usages table
    op.create_table(
        'machine_usages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('stage_id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=False),
        sa.Column('machine_id', sa.Uuid(), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('hours_used', sa.Numeric(precision=6, scale=2), nullable=False, server_default='0.00'),
        sa.Column('days_used', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('rate_applied', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('fuel_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('operator_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('bill_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['stage_id'], ['cultivation_stages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_usages_stage_id'), 'machine_usages', ['stage_id'], unique=False)
    op.create_index(op.f('ix_machine_usages_cultivation_id'), 'machine_usages', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_machine_usages_machine_id'), 'machine_usages', ['machine_id'], unique=False)
    op.create_index(op.f('ix_machine_usages_bill_id'), 'machine_usages', ['bill_id'], unique=False)
    op.create_index(op.f('ix_machine_usages_is_deleted'), 'machine_usages', ['is_deleted'], unique=False)

    # 9. material_purchases table
    op.create_table(
        'material_purchases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('purchase_code', sa.String(length=50), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=True),
        sa.Column('stage_id', sa.Uuid(), nullable=True),
        sa.Column('supplier_id', sa.Uuid(), nullable=False),
        sa.Column('material_category', sa.String(length=50), nullable=False, server_default='SEED'),
        sa.Column('material_name', sa.String(length=150), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=False, server_default='KG'),
        sa.Column('unit_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('payment_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('bill_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['cultivation_stages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_purchases_purchase_code'), 'material_purchases', ['purchase_code'], unique=False)
    op.create_index(op.f('ix_material_purchases_farmer_profile_id'), 'material_purchases', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_material_purchases_supplier_id'), 'material_purchases', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_material_purchases_cultivation_id'), 'material_purchases', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_material_purchases_stage_id'), 'material_purchases', ['stage_id'], unique=False)
    op.create_index(op.f('ix_material_purchases_bill_id'), 'material_purchases', ['bill_id'], unique=False)
    op.create_index(op.f('ix_material_purchases_is_deleted'), 'material_purchases', ['is_deleted'], unique=False)

    # 10. logistics table
    op.create_table(
        'logistics',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('dispatch_code', sa.String(length=50), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('cultivation_id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('harvest_location', sa.String(length=255), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('pickup_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vehicle_number', sa.String(length=50), nullable=False),
        sa.Column('driver_name', sa.String(length=150), nullable=False),
        sa.Column('driver_contact', sa.String(length=20), nullable=False),
        sa.Column('driver_id', sa.Uuid(), nullable=True),
        sa.Column('quantity_transported', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity_unit', sa.String(length=30), nullable=False, server_default='KG'),
        sa.Column('transport_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('loading_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('unloading_cost', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_logistics_cost', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PLANNED'),
        sa.Column('bill_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cultivation_id'], ['cultivation_runs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_logistics_dispatch_code'), 'logistics', ['dispatch_code'], unique=True)
    op.create_index(op.f('ix_logistics_farmer_profile_id'), 'logistics', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_logistics_cultivation_id'), 'logistics', ['cultivation_id'], unique=False)
    op.create_index(op.f('ix_logistics_farm_id'), 'logistics', ['farm_id'], unique=False)
    op.create_index(op.f('ix_logistics_driver_id'), 'logistics', ['driver_id'], unique=False)
    op.create_index(op.f('ix_logistics_is_deleted'), 'logistics', ['is_deleted'], unique=False)

    # 11. sms_logs table
    op.create_table(
        'sms_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('recipient_mobile', sa.String(length=20), nullable=False),
        sa.Column('recipient_name', sa.String(length=150), nullable=False),
        sa.Column('recipient_type', sa.String(length=30), nullable=False, server_default='WORKER'),
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False, server_default='WORK_COMPLETED_PAYMENT'),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='SENT'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gateway_response', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sms_logs_farmer_profile_id'), 'sms_logs', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_sms_logs_recipient_mobile'), 'sms_logs', ['recipient_mobile'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sms_logs_recipient_mobile'), table_name='sms_logs')
    op.drop_index(op.f('ix_sms_logs_farmer_profile_id'), table_name='sms_logs')
    op.drop_table('sms_logs')

    op.drop_index(op.f('ix_logistics_is_deleted'), table_name='logistics')
    op.drop_index(op.f('ix_logistics_driver_id'), table_name='logistics')
    op.drop_index(op.f('ix_logistics_farm_id'), table_name='logistics')
    op.drop_index(op.f('ix_logistics_cultivation_id'), table_name='logistics')
    op.drop_index(op.f('ix_logistics_farmer_profile_id'), table_name='logistics')
    op.drop_index(op.f('ix_logistics_dispatch_code'), table_name='logistics')
    op.drop_table('logistics')

    op.drop_index(op.f('ix_material_purchases_is_deleted'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_bill_id'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_stage_id'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_cultivation_id'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_supplier_id'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_farmer_profile_id'), table_name='material_purchases')
    op.drop_index(op.f('ix_material_purchases_purchase_code'), table_name='material_purchases')
    op.drop_table('material_purchases')

    op.drop_index(op.f('ix_machine_usages_is_deleted'), table_name='machine_usages')
    op.drop_index(op.f('ix_machine_usages_bill_id'), table_name='machine_usages')
    op.drop_index(op.f('ix_machine_usages_machine_id'), table_name='machine_usages')
    op.drop_index(op.f('ix_machine_usages_cultivation_id'), table_name='machine_usages')
    op.drop_index(op.f('ix_machine_usages_stage_id'), table_name='machine_usages')
    op.drop_table('machine_usages')

    op.drop_index(op.f('ix_worker_attendance_is_deleted'), table_name='worker_attendance')
    op.drop_index(op.f('ix_worker_attendance_bill_id'), table_name='worker_attendance')
    op.drop_index(op.f('ix_worker_attendance_worker_id'), table_name='worker_attendance')
    op.drop_index(op.f('ix_worker_attendance_cultivation_id'), table_name='worker_attendance')
    op.drop_index(op.f('ix_worker_attendance_stage_id'), table_name='worker_attendance')
    op.drop_table('worker_attendance')

    op.drop_index(op.f('ix_payments_is_deleted'), table_name='payments')
    op.drop_index(op.f('ix_payments_farmer_profile_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_bill_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_payment_number'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_bill_items_bill_id'), table_name='bill_items')
    op.drop_table('bill_items')

    op.drop_index(op.f('ix_bills_is_deleted'), table_name='bills')
    op.drop_index(op.f('ix_bills_recipient_supplier_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_recipient_worker_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_stage_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_cultivation_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_farm_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_farmer_profile_id'), table_name='bills')
    op.drop_index(op.f('ix_bills_bill_number'), table_name='bills')
    op.drop_table('bills')

    op.drop_index(op.f('ix_cultivation_schedules_is_deleted'), table_name='cultivation_schedules')
    op.drop_index(op.f('ix_cultivation_schedules_cultivation_id'), table_name='cultivation_schedules')
    op.drop_table('cultivation_schedules')

    op.drop_index(op.f('ix_machines_is_deleted'), table_name='machines')
    op.drop_index(op.f('ix_machines_is_active'), table_name='machines')
    op.drop_index(op.f('ix_machines_machine_name'), table_name='machines')
    op.drop_index(op.f('ix_machines_machine_code'), table_name='machines')
    op.drop_index(op.f('ix_machines_farmer_profile_id'), table_name='machines')
    op.drop_table('machines')

    op.drop_index(op.f('ix_workers_is_deleted'), table_name='workers')
    op.drop_index(op.f('ix_workers_is_active'), table_name='workers')
    op.drop_index(op.f('ix_workers_user_id'), table_name='workers')
    op.drop_index(op.f('ix_workers_mobile_number'), table_name='workers')
    op.drop_index(op.f('ix_workers_full_name'), table_name='workers')
    op.drop_index(op.f('ix_workers_worker_code'), table_name='workers')
    op.drop_index(op.f('ix_workers_farmer_profile_id'), table_name='workers')
    op.drop_table('workers')
