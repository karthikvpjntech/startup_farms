"""add location fields to farmer profiles

Revision ID: 0010_farmer_profile_location
Revises: 0009_livestock_and_marketplace
Create Date: 2026-09-19 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0010_farmer_profile_location'
down_revision: Union[str, None] = '0009_livestock_and_marketplace'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('farmer_profiles', sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('farmer_profiles', sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('farmer_profiles', sa.Column('location_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('farmer_profiles', 'location_url')
    op.drop_column('farmer_profiles', 'longitude')
    op.drop_column('farmer_profiles', 'latitude')
