"""create role profile tables

Revision ID: 0003_role_profiles
Revises: 0002_refresh_tokens
Create Date: 2026-09-07 21:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003_role_profiles'
down_revision: Union[str, None] = '0002_refresh_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'farmer_profiles'
    op.create_table(
        'farmer_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('profile_image_url', sa.String(length=500), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('village', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_farmer_profiles_user_id')
    )
    op.create_index(op.f('ix_farmer_profiles_user_id'), 'farmer_profiles', ['user_id'], unique=True)

    # 2. Create 'trader_profiles'
    op.create_table(
        'trader_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('business_registration_number', sa.String(length=100), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_trader_profiles_user_id')
    )
    op.create_index(op.f('ix_trader_profiles_user_id'), 'trader_profiles', ['user_id'], unique=True)

    # 3. Create 'driver_profiles'
    op.create_table(
        'driver_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('license_number', sa.String(length=100), nullable=True),
        sa.Column('license_expiry_date', sa.Date(), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_driver_profiles_user_id')
    )
    op.create_index(op.f('ix_driver_profiles_user_id'), 'driver_profiles', ['user_id'], unique=True)

    # 4. Create 'worker_profiles'
    op.create_table(
        'worker_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_worker_profiles_user_id')
    )
    op.create_index(op.f('ix_worker_profiles_user_id'), 'worker_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_worker_profiles_user_id'), table_name='worker_profiles')
    op.drop_table('worker_profiles')
    op.drop_index(op.f('ix_driver_profiles_user_id'), table_name='driver_profiles')
    op.drop_table('driver_profiles')
    op.drop_index(op.f('ix_trader_profiles_user_id'), table_name='trader_profiles')
    op.drop_table('trader_profiles')
    op.drop_index(op.f('ix_farmer_profiles_user_id'), table_name='farmer_profiles')
    op.drop_table('farmer_profiles')
