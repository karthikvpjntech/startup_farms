"""add pickup location, maps url and instructions to produce procurements

Revision ID: 0012_produce_pickup_location
Revises: 0011_crop_plan_seed_options
Create Date: 2026-09-25 08:37:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0012_produce_pickup_location'
down_revision: Union[str, None] = '0011_crop_plan_seed_options'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'produce_procurements' in inspector.get_table_names():
        op.add_column('produce_procurements', sa.Column('pickup_location', sa.Text(), nullable=True))
        op.add_column('produce_procurements', sa.Column('google_maps_url', sa.String(length=500), nullable=True))
        op.add_column('produce_procurements', sa.Column('pickup_instructions', sa.Text(), nullable=True))
        op.add_column('produce_procurements', sa.Column('estimated_pickup_date', sa.Date(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'produce_procurements' in inspector.get_table_names():
        op.drop_column('produce_procurements', 'estimated_pickup_date')
        op.drop_column('produce_procurements', 'pickup_instructions')
        op.drop_column('produce_procurements', 'google_maps_url')
        op.drop_column('produce_procurements', 'pickup_location')

