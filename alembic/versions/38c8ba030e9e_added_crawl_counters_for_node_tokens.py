"""added crawl counters for node tokens

Revision ID: 38c8ba030e9e
Revises: e7cf803e5f09
Create Date: 2024-10-09 11:50:49.271257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38c8ba030e9e'
down_revision: Union[str, None] = 'e7cf803e5f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('crawl_counters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('node_token_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('uses', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['node_token_id'], ['node_tokens.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('node_token_id', 'date', name='uix_node_token_date')
    )
    op.create_index(op.f('ix_crawl_counters_id'), 'crawl_counters', ['id'], unique=False)
    op.add_column('node_tokens', sa.Column('crawl_daily_limit', sa.Integer(), nullable=True))
    op.add_column('node_tokens', sa.Column('can_view_receipt_images', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('node_tokens', 'can_view_receipt_images')
    op.drop_column('node_tokens', 'crawl_daily_limit')
    op.drop_index(op.f('ix_crawl_counters_id'), table_name='crawl_counters')
    op.drop_table('crawl_counters')
    # ### end Alembic commands ###
