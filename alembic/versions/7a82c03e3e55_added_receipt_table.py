"""added receipt table

Revision ID: 7a82c03e3e55
Revises: ddaedc2d31b1
Create Date: 2024-10-13 14:48:53.334805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a82c03e3e55'
down_revision: Union[str, None] = 'ddaedc2d31b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('receipts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('WAITING', 'PROCESSING', 'COMPLETED', 'CANCELED', 'FAILED', name='receiptstatus'), nullable=False),
    sa.Column('purchase_id', sa.Integer(), nullable=True),
    sa.Column('image_url', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('image_url')
    )
    op.create_index(op.f('ix_receipts_id'), 'receipts', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_receipts_id'), table_name='receipts')
    op.drop_table('receipts')
    # ### end Alembic commands ###
