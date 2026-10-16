"""create livestock and marketplace tables

Revision ID: 0009_livestock_and_marketplace
Revises: 0008_farmer_crm_operations
Create Date: 2026-09-18 09:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0009_livestock_and_marketplace'
down_revision: Union[str, None] = '0008_farmer_crm_operations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. livestock_categories
    op.create_table(
        'livestock_categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_ta', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_slug', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_livestock_categories_code')
    )
    op.create_index(op.f('ix_livestock_categories_code'), 'livestock_categories', ['code'], unique=True)
    op.create_index(op.f('ix_livestock_categories_is_active'), 'livestock_categories', ['is_active'], unique=False)

    # 2. livestock_breeds
    op.create_table(
        'livestock_breeds',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_ta', sa.String(length=150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('characteristics', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['livestock_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'name', name='uq_livestock_breed_category_name')
    )
    op.create_index(op.f('ix_livestock_breeds_category_id'), 'livestock_breeds', ['category_id'], unique=False)
    op.create_index(op.f('ix_livestock_breeds_code'), 'livestock_breeds', ['code'], unique=False)
    op.create_index(op.f('ix_livestock_breeds_is_active'), 'livestock_breeds', ['is_active'], unique=False)

    # 3. livestock
    op.create_table(
        'livestock',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('livestock_code', sa.String(length=50), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=False),
        sa.Column('breed_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tag_number', sa.String(length=100), nullable=True),
        sa.Column('selling_model', sa.String(length=30), server_default='INDIVIDUAL', nullable=False),
        sa.Column('gender', sa.String(length=30), server_default='UNKNOWN', nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('age', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('age_unit', sa.String(length=20), nullable=True),
        sa.Column('weight', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('weight_unit', sa.String(length=20), server_default='KG', nullable=True),
        sa.Column('health_status', sa.String(length=50), server_default='HEALTHY', nullable=False),
        sa.Column('vaccination_status', sa.String(length=50), server_default='UP_TO_DATE', nullable=False),
        sa.Column('vaccination_date', sa.Date(), nullable=True),
        sa.Column('health_certificate_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_summary', sa.String(length=255), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('price_type', sa.String(length=30), server_default='PER_UNIT', nullable=False),
        sa.Column('available_quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('minimum_order_quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('maximum_order_quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='DRAFT', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.CheckConstraint('available_quantity >= 0', name='chk_livestock_avail_qty_non_negative'),
        sa.CheckConstraint('price >= 0', name='chk_livestock_price_non_negative'),
        sa.CheckConstraint('minimum_order_quantity >= 1', name='chk_livestock_min_order_qty_positive'),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['category_id'], ['livestock_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['breed_id'], ['livestock_breeds.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('livestock_code', name='uq_livestock_code')
    )
    op.create_index(op.f('ix_livestock_livestock_code'), 'livestock', ['livestock_code'], unique=True)
    op.create_index(op.f('ix_livestock_farmer_profile_id'), 'livestock', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_livestock_farm_id'), 'livestock', ['farm_id'], unique=False)
    op.create_index(op.f('ix_livestock_category_id'), 'livestock', ['category_id'], unique=False)
    op.create_index(op.f('ix_livestock_breed_id'), 'livestock', ['breed_id'], unique=False)
    op.create_index(op.f('ix_livestock_tag_number'), 'livestock', ['tag_number'], unique=False)
    op.create_index(op.f('ix_livestock_status'), 'livestock', ['status'], unique=False)
    op.create_index(op.f('ix_livestock_is_active'), 'livestock', ['is_active'], unique=False)
    op.create_index(op.f('ix_livestock_is_deleted'), 'livestock', ['is_deleted'], unique=False)
    op.create_index('ix_livestock_status_active_deleted', 'livestock', ['status', 'is_active', 'is_deleted'], unique=False)
    op.create_index('ix_livestock_category_price', 'livestock', ['category_id', 'price'], unique=False)

    # 4. livestock_images
    op.create_table(
        'livestock_images',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('livestock_id', sa.Uuid(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('image_type', sa.String(length=30), server_default='MAIN', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['livestock_id'], ['livestock.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_livestock_images_livestock_id'), 'livestock_images', ['livestock_id'], unique=False)

    # 5. carts
    op.create_table(
        'carts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_carts_user_id')
    )
    op.create_index(op.f('ix_carts_user_id'), 'carts', ['user_id'], unique=True)

    # 6. cart_items
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('cart_id', sa.Uuid(), nullable=False),
        sa.Column('livestock_id', sa.Uuid(), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('quantity >= 1', name='chk_cart_item_quantity_positive'),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['livestock_id'], ['livestock.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cart_id', 'livestock_id', name='uq_cart_items_cart_livestock')
    )
    op.create_index(op.f('ix_cart_items_cart_id'), 'cart_items', ['cart_id'], unique=False)
    op.create_index(op.f('ix_cart_items_livestock_id'), 'cart_items', ['livestock_id'], unique=False)

    # 7. marketplace_orders
    op.create_table(
        'marketplace_orders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Uuid(), nullable=False),
        sa.Column('farmer_profile_id', sa.Uuid(), nullable=False),
        sa.Column('total_items_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('subtotal_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('delivery_charge', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('payment_status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('delivery_type', sa.String(length=30), server_default='FARM_PICKUP', nullable=False),
        sa.Column('delivery_contact_name', sa.String(length=150), nullable=False),
        sa.Column('delivery_contact_phone', sa.String(length=20), nullable=False),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('delivery_city', sa.String(length=100), nullable=True),
        sa.Column('delivery_pincode', sa.String(length=10), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.CheckConstraint('total_amount >= 0', name='chk_marketplace_order_total_non_negative'),
        sa.CheckConstraint('subtotal_amount >= 0', name='chk_marketplace_order_subtotal_non_negative'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['farmer_profile_id'], ['farmer_profiles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number', name='uq_marketplace_orders_order_number')
    )
    op.create_index(op.f('ix_marketplace_orders_order_number'), 'marketplace_orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_marketplace_orders_customer_id'), 'marketplace_orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_marketplace_orders_farmer_profile_id'), 'marketplace_orders', ['farmer_profile_id'], unique=False)
    op.create_index(op.f('ix_marketplace_orders_status'), 'marketplace_orders', ['status'], unique=False)
    op.create_index(op.f('ix_marketplace_orders_payment_status'), 'marketplace_orders', ['payment_status'], unique=False)
    op.create_index(op.f('ix_marketplace_orders_is_deleted'), 'marketplace_orders', ['is_deleted'], unique=False)
    op.create_index('ix_marketplace_orders_customer_created', 'marketplace_orders', ['customer_id', 'created_at'], unique=False)
    op.create_index('ix_marketplace_orders_farmer_status', 'marketplace_orders', ['farmer_profile_id', 'status'], unique=False)

    # 8. marketplace_order_items
    op.create_table(
        'marketplace_order_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('livestock_id', sa.Uuid(), nullable=False),
        sa.Column('farm_id', sa.Uuid(), nullable=False),
        sa.Column('livestock_name', sa.String(length=255), nullable=False),
        sa.Column('livestock_code', sa.String(length=50), nullable=False),
        sa.Column('category_name', sa.String(length=100), nullable=False),
        sa.Column('breed_name', sa.String(length=100), nullable=True),
        sa.Column('tag_number', sa.String(length=100), nullable=True),
        sa.Column('selling_model', sa.String(length=30), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('unit_price >= 0', name='chk_order_item_unit_price_non_negative'),
        sa.CheckConstraint('quantity >= 1', name='chk_order_item_qty_positive'),
        sa.CheckConstraint('subtotal >= 0', name='chk_order_item_subtotal_non_negative'),
        sa.ForeignKeyConstraint(['order_id'], ['marketplace_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['livestock_id'], ['livestock.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketplace_order_items_order_id'), 'marketplace_order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_marketplace_order_items_livestock_id'), 'marketplace_order_items', ['livestock_id'], unique=False)
    op.create_index(op.f('ix_marketplace_order_items_farm_id'), 'marketplace_order_items', ['farm_id'], unique=False)

    # 9. marketplace_payments
    op.create_table(
        'marketplace_payments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('customer_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), server_default='UPI', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('transaction_reference', sa.String(length=100), nullable=True),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['marketplace_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_marketplace_payments_order_id'),
        sa.UniqueConstraint('payment_number', name='uq_marketplace_payments_number')
    )
    op.create_index(op.f('ix_marketplace_payments_payment_number'), 'marketplace_payments', ['payment_number'], unique=True)
    op.create_index(op.f('ix_marketplace_payments_order_id'), 'marketplace_payments', ['order_id'], unique=True)
    op.create_index(op.f('ix_marketplace_payments_customer_id'), 'marketplace_payments', ['customer_id'], unique=False)

    # 10. marketplace_deliveries
    op.create_table(
        'marketplace_deliveries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('delivery_code', sa.String(length=50), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('driver_id', sa.Uuid(), nullable=True),
        sa.Column('pickup_location', sa.String(length=255), nullable=False),
        sa.Column('drop_location', sa.String(length=255), nullable=False),
        sa.Column('scheduled_pickup', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vehicle_number', sa.String(length=50), nullable=True),
        sa.Column('driver_name', sa.String(length=150), nullable=True),
        sa.Column('driver_contact', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('tracking_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['marketplace_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('delivery_code', name='uq_marketplace_deliveries_code'),
        sa.UniqueConstraint('order_id', name='uq_marketplace_deliveries_order_id')
    )
    op.create_index(op.f('ix_marketplace_deliveries_delivery_code'), 'marketplace_deliveries', ['delivery_code'], unique=True)
    op.create_index(op.f('ix_marketplace_deliveries_order_id'), 'marketplace_deliveries', ['order_id'], unique=True)
    op.create_index(op.f('ix_marketplace_deliveries_driver_id'), 'marketplace_deliveries', ['driver_id'], unique=False)

    # 11. livestock_reviews
    op.create_table(
        'livestock_reviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('livestock_id', sa.Uuid(), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('customer_id', sa.Uuid(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='chk_livestock_review_rating_1_to_5'),
        sa.ForeignKeyConstraint(['livestock_id'], ['livestock.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['marketplace_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', 'livestock_id', 'customer_id', name='uq_livestock_review_order_item_customer')
    )
    op.create_index(op.f('ix_livestock_reviews_livestock_id'), 'livestock_reviews', ['livestock_id'], unique=False)
    op.create_index(op.f('ix_livestock_reviews_order_id'), 'livestock_reviews', ['order_id'], unique=False)
    op.create_index(op.f('ix_livestock_reviews_customer_id'), 'livestock_reviews', ['customer_id'], unique=False)


def downgrade() -> None:
    op.drop_table('livestock_reviews')
    op.drop_table('marketplace_deliveries')
    op.drop_table('marketplace_payments')
    op.drop_table('marketplace_order_items')
    op.drop_table('marketplace_orders')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('livestock_images')
    op.drop_table('livestock')
    op.drop_table('livestock_breeds')
    op.drop_table('livestock_categories')
