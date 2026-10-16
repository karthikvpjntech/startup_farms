"""add seed variety, rate and memory reminder fields to farm crop plans

Revision ID: 0011_crop_plan_seed_options
Revises: 0010_farmer_profile_location
Create Date: 2026-09-25 08:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0011_crop_plan_seed_options'
down_revision: Union[str, None] = '0010_farmer_profile_location'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('farm_crop_plans', sa.Column('seed_variety', sa.String(length=100), nullable=True))
    op.add_column('farm_crop_plans', sa.Column('seed_rate_per_acre', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('farm_crop_plans', sa.Column('seed_rate_unit', sa.String(length=30), nullable=True, server_default='kg/acre'))
    op.add_column('farm_crop_plans', sa.Column('total_seed_quantity', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('farm_crop_plans', sa.Column('sowing_method', sa.String(length=50), nullable=True, server_default='DIRECT_SEEDING'))
    op.add_column('farm_crop_plans', sa.Column('seed_brand_or_source', sa.String(length=150), nullable=True))
    op.add_column('farm_crop_plans', sa.Column('remind_next_year', sa.Boolean(), nullable=False, server_default=sa.text('true')))


def downgrade() -> None:
    op.drop_column('farm_crop_plans', 'remind_next_year')
    op.drop_column('farm_crop_plans', 'seed_brand_or_source')
    op.drop_column('farm_crop_plans', 'sowing_method')
    op.drop_column('farm_crop_plans', 'total_seed_quantity')
    op.drop_column('farm_crop_plans', 'seed_rate_unit')
    op.drop_column('farm_crop_plans', 'seed_rate_per_acre')
    op.drop_column('farm_crop_plans', 'seed_variety')
