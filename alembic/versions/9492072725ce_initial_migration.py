"""Initial migration

Revision ID: 9492072725ce
Revises: 
Create Date: 2024-09-15 16:56:09.740498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9492072725ce'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('purchases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('read_entity_name', sa.String(length=255), nullable=True),
    sa.Column('read_entity_branch', sa.String(length=255), nullable=True),
    sa.Column('read_entity_location', sa.String(length=255), nullable=True),
    sa.Column('read_entity_address', sa.String(length=255), nullable=True),
    sa.Column('read_entity_identification', sa.String(length=255), nullable=True),
    sa.Column('read_entity_phone', sa.String(length=255), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('subtotal', sa.Float(), nullable=True),
    sa.Column('discount', sa.Float(), nullable=True),
    sa.Column('tips', sa.Float(), nullable=True),
    sa.Column('total', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchases_id'), 'purchases', ['id'], unique=False)
    op.create_table('purchase_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('purchase_id', sa.Integer(), nullable=False),
    sa.Column('read_product_key', sa.String(length=255), nullable=True),
    sa.Column('read_product_text', sa.String(length=255), nullable=True),
    sa.Column('quantity', sa.Float(), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('total', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_items_id'), 'purchase_items', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_purchase_items_id'), table_name='purchase_items')
    op.drop_table('purchase_items')
    op.drop_index(op.f('ix_purchases_id'), table_name='purchases')
    op.drop_table('purchases')
    # ### end Alembic commands ###