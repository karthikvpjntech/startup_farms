"""create farms table

Revision ID: 0004_farms
Revises: 0003_role_profiles
Create Date: 2026-09-08 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004_farms'
down_revision: Union[str, None] = '0003_role_profiles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'farms' table
    op.create_table(
        'farms',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('farm_name', sa.String(length=255), nullable=False),
        sa.Column('farm_code', sa.String(length=50), nullable=False),
        sa.Column('ownership_type', sa.String(length=50), nullable=False),
        sa.Column('total_land_area', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('land_area_unit', sa.String(length=50), nullable=False),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('village', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_code', name='uq_farms_farm_code')
    )
    op.create_index(op.f('ix_farms_farmer_profile_id'), 'farms', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_farms_farm_code'), 'farms', ['farm_code'], unique=True)
    op.create_index(op.f('ix_farms_is_active'), 'farms', ['is_active'], unique=False)
    op.create_index(op.f('ix_farms_is_deleted'), 'farms', ['is_deleted'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_farms_is_deleted'), table_name='farms')
    op.drop_index(op.f('ix_farms_is_active'), table_name='farms')
    op.drop_index(op.f('ix_farms_farm_code'), table_name='farms')
    op.drop_index(op.f('ix_farms_farmer_profile_id'), table_name='farms')
    op.drop_table('farms')
