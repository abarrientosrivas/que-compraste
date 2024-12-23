"""added category relation to product

Revision ID: 2de0f00a7686
Revises: 526964df6606
Create Date: 2024-10-02 15:21:30.535185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2de0f00a7686'
down_revision: Union[str, None] = '526964df6606'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'products', 'categories', ['category_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.drop_column('products', 'category_id')
    # ### end Alembic commands ###
