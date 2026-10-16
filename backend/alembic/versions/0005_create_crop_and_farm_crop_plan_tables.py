"""create crop and farm_crop_plan tables

Revision ID: 0005_crops_and_plans
Revises: 0004_farms
Create Date: 2026-09-08 21:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0005_crops_and_plans'
down_revision: Union[str, None] = '0004_farms'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'crops' table
    op.create_table(
        'crops',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('crop_name', sa.String(length=100), nullable=False),
        sa.Column('crop_code', sa.String(length=50), nullable=False),
        sa.Column('scientific_name', sa.String(length=150), nullable=True),
        sa.Column('crop_category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crop_code', name='uq_crops_crop_code')
    )
    op.create_index(op.f('ix_crops_crop_code'), 'crops', ['crop_code'], unique=True)
    op.create_index(
        'ix_crops_name_category_not_deleted',
        'crops',
        ['crop_name', 'crop_category'],
        unique=False,
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(
        'ix_crops_active_not_deleted',
        'crops',
        ['is_active'],
        unique=False,
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(op.f('ix_crops_is_active'), 'crops', ['is_active'], unique=False)
    op.create_index(op.f('ix_crops_is_deleted'), 'crops', ['is_deleted'], unique=False)

    # 2. Create 'farm_crop_plans' table
    op.create_table(
        'farm_crop_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('crop_id', sa.Uuid(), nullable=False),
        sa.Column('season', sa.String(length=50), nullable=False),
        sa.Column('planned_start_date', sa.Date(), nullable=False),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('planned_area', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('land_area_unit', sa.String(length=30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.CheckConstraint('planned_area > 0', name='chk_farm_crop_plans_planned_area'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_farm_crop_plans_farm_id'), 'farm_crop_plans', ['farm_id'], unique=False)
    op.create_index(op.f('ix_farm_crop_plans_crop_id'), 'farm_crop_plans', ['crop_id'], unique=False)
    op.create_index(
        'uq_active_farm_crop_season',
        'farm_crop_plans',
        ['farm_id', 'crop_id', 'season'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND is_active = true')
    )
    op.create_index(
        'ix_farm_crop_plans_farm_active_not_deleted',
        'farm_crop_plans',
        ['farm_id', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(op.f('ix_farm_crop_plans_season'), 'farm_crop_plans', ['season'], unique=False)
    op.create_index(op.f('ix_farm_crop_plans_is_active'), 'farm_crop_plans', ['is_active'], unique=False)
    op.create_index(op.f('ix_farm_crop_plans_is_deleted'), 'farm_crop_plans', ['is_deleted'], unique=False)


def downgrade() -> None:
    # 1. Drop child table (farm_crop_plans) indexes and table first
    op.drop_index(op.f('ix_farm_crop_plans_is_deleted'), table_name='farm_crop_plans')
    op.drop_index(op.f('ix_farm_crop_plans_is_active'), table_name='farm_crop_plans')
    op.drop_index(op.f('ix_farm_crop_plans_season'), table_name='farm_crop_plans')
    op.drop_index('ix_farm_crop_plans_farm_active_not_deleted', table_name='farm_crop_plans')
    op.drop_index('uq_active_farm_crop_season', table_name='farm_crop_plans')
    op.drop_index(op.f('ix_farm_crop_plans_crop_id'), table_name='farm_crop_plans')
    op.drop_index(op.f('ix_farm_crop_plans_farm_id'), table_name='farm_crop_plans')
    op.drop_table('farm_crop_plans')

    # 2. Drop parent table (crops) indexes and table
    op.drop_index(op.f('ix_crops_is_deleted'), table_name='crops')
    op.drop_index(op.f('ix_crops_is_active'), table_name='crops')
    op.drop_index('ix_crops_active_not_deleted', table_name='crops')
    op.drop_index('ix_crops_name_category_not_deleted', table_name='crops')
    op.drop_index(op.f('ix_crops_crop_code'), table_name='crops')
    op.drop_table('crops')

