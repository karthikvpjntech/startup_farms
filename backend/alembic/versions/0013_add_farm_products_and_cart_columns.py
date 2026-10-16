"""add farm products and cart columns

Revision ID: 0013_farm_products_cart_columns
Revises: 0012_produce_pickup_location
Create Date: 2026-09-27 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0013_farm_products_cart_columns'
down_revision: Union[str, None] = '0012_produce_pickup_location'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'marketplace_order_items' in tables:
        cols = [c['name'] for c in inspector.get_columns('marketplace_order_items')]
        if 'farm_product_id' not in cols:
            op.add_column('marketplace_order_items', sa.Column('farm_product_id', sa.Uuid(), nullable=True))
        if 'product_type' not in cols:
            op.add_column('marketplace_order_items', sa.Column('product_type', sa.String(length=30), server_default='LIVESTOCK', nullable=False))
        if 'variety_name' not in cols:
            op.add_column('marketplace_order_items', sa.Column('variety_name', sa.String(length=150), nullable=True))
        if 'unit' not in cols:
            op.add_column('marketplace_order_items', sa.Column('unit', sa.String(length=50), nullable=True))

    if 'cart_items' in tables:
        cols = [c['name'] for c in inspector.get_columns('cart_items')]
        if 'farm_product_id' not in cols:
            op.add_column('cart_items', sa.Column('farm_product_id', sa.Uuid(), nullable=True))
        if 'product_type' not in cols:
            op.add_column('cart_items', sa.Column('product_type', sa.String(length=30), server_default='LIVESTOCK', nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'cart_items' in tables:
        cols = [c['name'] for c in inspector.get_columns('cart_items')]
        if 'product_type' in cols:
            op.drop_column('cart_items', 'product_type')
        if 'farm_product_id' in cols:
            op.drop_column('cart_items', 'farm_product_id')

    if 'marketplace_order_items' in tables:
        cols = [c['name'] for c in inspector.get_columns('marketplace_order_items')]
        if 'unit' in cols:
            op.drop_column('marketplace_order_items', 'unit')
        if 'variety_name' in cols:
            op.drop_column('marketplace_order_items', 'variety_name')
        if 'product_type' in cols:
            op.drop_column('marketplace_order_items', 'product_type')
        if 'farm_product_id' in cols:
            op.drop_column('marketplace_order_items', 'farm_product_id')
