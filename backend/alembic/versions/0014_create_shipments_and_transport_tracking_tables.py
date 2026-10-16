"""create shipments and transport tracking tables

Revision ID: 0014_shipments_transport_tracking
Revises: 0013_farm_products_cart_columns
Create Date: 2026-10-06 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0014_shipments_transport_tracking'
down_revision: Union[str, None] = '0013_farm_products_cart_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. transport_providers
    if 'transport_providers' not in tables:
        op.create_table(
            'transport_providers',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('provider_name', sa.String(length=150), nullable=False, index=True),
            sa.Column('provider_code', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('contact_person', sa.String(length=150), nullable=True),
            sa.Column('phone_number', sa.String(length=20), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('vehicle_type', sa.String(length=50), nullable=True),
            sa.Column('vehicle_number', sa.String(length=50), nullable=True),
            sa.Column('service_areas', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 2. shipments
    if 'shipments' not in tables:
        op.create_table(
            'shipments',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('shipment_number', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('tracking_number', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('order_id', sa.Uuid(), sa.ForeignKey('marketplace_orders.id', ondelete='RESTRICT'), nullable=False, index=True),
            sa.Column('farmer_profile_id', sa.Uuid(), sa.ForeignKey('farmer_profiles.id', ondelete='RESTRICT'), nullable=False, index=True),
            sa.Column('customer_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True),
            sa.Column('transport_provider_id', sa.Uuid(), sa.ForeignKey('transport_providers.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('driver_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('current_status', sa.String(length=40), server_default='CREATED', nullable=False, index=True),
            sa.Column('current_location', sa.String(length=255), nullable=True),
            sa.Column('origin_address', sa.Text(), nullable=False),
            sa.Column('origin_city', sa.String(length=100), nullable=False),
            sa.Column('origin_pincode', sa.String(length=10), nullable=False),
            sa.Column('destination_address', sa.Text(), nullable=False),
            sa.Column('destination_city', sa.String(length=100), nullable=False),
            sa.Column('destination_pincode', sa.String(length=10), nullable=False),
            sa.Column('total_packages', sa.Integer(), server_default='1', nullable=False),
            sa.Column('total_weight_kg', sa.Numeric(precision=10, scale=2), server_default='1.00', nullable=False),
            sa.Column('is_perishable', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('special_handling', sa.String(length=50), server_default='GENERAL', nullable=False),
            sa.Column('barcode_data', sa.String(length=100), nullable=False),
            sa.Column('qr_code_data', sa.Text(), nullable=False),
            sa.Column('estimated_delivery_date', sa.Date(), nullable=True),
            sa.Column('actual_delivery_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 3. shipment_packages
    if 'shipment_packages' not in tables:
        op.create_table(
            'shipment_packages',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('shipment_id', sa.Uuid(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('package_number', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('package_barcode', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('item_description', sa.String(length=255), nullable=False),
            sa.Column('weight_kg', sa.Numeric(precision=8, scale=2), server_default='1.00', nullable=False),
            sa.Column('package_type', sa.String(length=50), server_default='CORRUGATED_CARTON', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 4. shipment_tracking_events
    if 'shipment_tracking_events' not in tables:
        op.create_table(
            'shipment_tracking_events',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('shipment_id', sa.Uuid(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('status', sa.String(length=40), nullable=False, index=True),
            sa.Column('location_hub', sa.String(length=255), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('remarks', sa.Text(), nullable=True),
            sa.Column('updated_by_user_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('updated_by_role', sa.String(length=50), nullable=True),
            sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 5. pickup_requests
    if 'pickup_requests' not in tables:
        op.create_table(
            'pickup_requests',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('pickup_code', sa.String(length=50), unique=True, nullable=False, index=True),
            sa.Column('shipment_id', sa.Uuid(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('farmer_profile_id', sa.Uuid(), sa.ForeignKey('farmer_profiles.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('pickup_address', sa.Text(), nullable=False),
            sa.Column('pickup_contact_name', sa.String(length=150), nullable=False),
            sa.Column('pickup_contact_phone', sa.String(length=20), nullable=False),
            sa.Column('scheduled_date', sa.Date(), nullable=False),
            sa.Column('time_window', sa.String(length=50), server_default='MORNING_7_11', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False, index=True),
            sa.Column('assigned_driver_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('assigned_vehicle_number', sa.String(length=50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 6. delivery_attempts
    if 'delivery_attempts' not in tables:
        op.create_table(
            'delivery_attempts',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('shipment_id', sa.Uuid(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
            sa.Column('attempt_status', sa.String(length=30), server_default='SUCCESS', nullable=False),
            sa.Column('failure_reason', sa.String(length=100), nullable=True),
            sa.Column('recipient_name', sa.String(length=150), nullable=True),
            sa.Column('recipient_signature_note', sa.Text(), nullable=True),
            sa.Column('driver_notes', sa.Text(), nullable=True),
            sa.Column('attempt_time', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'delivery_attempts' in tables:
        op.drop_table('delivery_attempts')
    if 'pickup_requests' in tables:
        op.drop_table('pickup_requests')
    if 'shipment_tracking_events' in tables:
        op.drop_table('shipment_tracking_events')
    if 'shipment_packages' in tables:
        op.drop_table('shipment_packages')
    if 'shipments' in tables:
        op.drop_table('shipments')
    if 'transport_providers' in tables:
        op.drop_table('transport_providers')
