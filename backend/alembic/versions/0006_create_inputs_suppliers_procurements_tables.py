"""create input_masters, suppliers, and procurement_requests tables

Revision ID: 0006_inputs_suppliers_procurements
Revises: 0005_crops_and_plans
Create Date: 2026-09-10 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0006_inputs_suppliers_procurements'
down_revision: Union[str, None] = '0005_crops_and_plans'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create input_masters table
    op.create_table(
        'input_masters',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('input_code', sa.String(length=50), nullable=False),
        sa.Column('input_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=False),
        sa.Column('technical_name', sa.String(length=200), nullable=True),
        sa.Column('brand_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('input_code', name='uq_input_masters_input_code')
    )
    op.create_index(op.f('ix_input_masters_input_code'), 'input_masters', ['input_code'], unique=True)
    op.create_index(op.f('ix_input_masters_input_name'), 'input_masters', ['input_name'], unique=False)
    op.create_index(op.f('ix_input_masters_category'), 'input_masters', ['category'], unique=False)
    op.create_index(op.f('ix_input_masters_is_active'), 'input_masters', ['is_active'], unique=False)
    op.create_index(op.f('ix_input_masters_is_deleted'), 'input_masters', ['is_deleted'], unique=False)

    # 2. Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=False),
        sa.Column('supplier_name', sa.String(length=150), nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('village_city', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=20), nullable=False),
        sa.Column('gstin', sa.String(length=30), nullable=True),
        sa.Column('supplier_type', sa.String(length=50), server_default='DISTRIBUTOR', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_code', name='uq_suppliers_supplier_code')
    )
    op.create_index(op.f('ix_suppliers_supplier_code'), 'suppliers', ['supplier_code'], unique=True)
    op.create_index(op.f('ix_suppliers_supplier_name'), 'suppliers', ['supplier_name'], unique=False)
    op.create_index(op.f('ix_suppliers_phone_number'), 'suppliers', ['phone_number'], unique=False)
    op.create_index(op.f('ix_suppliers_district'), 'suppliers', ['district'], unique=False)
    op.create_index(op.f('ix_suppliers_state'), 'suppliers', ['state'], unique=False)
    op.create_index(op.f('ix_suppliers_is_active'), 'suppliers', ['is_active'], unique=False)
    op.create_index(op.f('ix_suppliers_is_deleted'), 'suppliers', ['is_deleted'], unique=False)

    # 3. Create procurement_requests table
    op.create_table(
        'procurement_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('request_code', sa.String(length=50), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('input_id', sa.Uuid(), nullable=False),
        sa.Column('preferred_supplier_id', sa.Uuid(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=False),
        sa.Column('required_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['input_id'], ['input_masters.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['preferred_supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_code', name='uq_procurement_requests_request_code')
    )
    op.create_index(op.f('ix_procurement_requests_request_code'), 'procurement_requests', ['request_code'], unique=True)
    op.create_index(op.f('ix_procurement_requests_farmer_profile_id'), 'procurement_requests', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_procurement_requests_farm_id'), 'procurement_requests', ['farm_id'], unique=False)
    op.create_index(op.f('ix_procurement_requests_input_id'), 'procurement_requests', ['input_id'], unique=False)
    op.create_index(op.f('ix_procurement_requests_preferred_supplier_id'), 'procurement_requests', ['preferred_supplier_id'], unique=False)
    op.create_index(op.f('ix_procurement_requests_status'), 'procurement_requests', ['status'], unique=False)
    op.create_index(op.f('ix_procurement_requests_is_deleted'), 'procurement_requests', ['is_deleted'], unique=False)


def downgrade() -> None:
    op.drop_table('procurement_requests')
    op.drop_table('suppliers')
    op.drop_table('input_masters')
