"""create crop_cultivation_stages table

Revision ID: 0007_crop_cultivation_stages
Revises: 0006_inputs_suppliers_procurements
Create Date: 2026-09-14 17:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0007_crop_cultivation_stages'
down_revision: Union[str, None] = '0006_inputs_suppliers_procurements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crop_cultivation_stages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('crop_id', sa.Uuid(), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(length=200), nullable=False),
        sa.Column('stage_name_local', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('visual_asset_type', sa.String(length=50), nullable=False, server_default='VEGETATIVE'),
        sa.Column('visual_theme_color', sa.String(length=20), nullable=False, server_default='#10b981'),
        sa.Column('recommended_activities', sa.JSON(), nullable=False),
        sa.Column('recommended_inputs', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_cultivation_stages_crop_id'), 'crop_cultivation_stages', ['crop_id'], unique=False)
    op.create_index(op.f('ix_crop_cultivation_stages_is_active'), 'crop_cultivation_stages', ['is_active'], unique=False)
    op.create_index(op.f('ix_crop_cultivation_stages_is_deleted'), 'crop_cultivation_stages', ['is_deleted'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_crop_cultivation_stages_is_deleted'), table_name='crop_cultivation_stages')
    op.drop_index(op.f('ix_crop_cultivation_stages_is_active'), table_name='crop_cultivation_stages')
    op.drop_index(op.f('ix_crop_cultivation_stages_crop_id'), table_name='crop_cultivation_stages')
    op.drop_table('crop_cultivation_stages')
