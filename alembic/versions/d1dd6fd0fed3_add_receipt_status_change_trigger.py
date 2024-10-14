"""add receipt status change trigger

Revision ID: d1dd6fd0fed3
Revises: e707670ab1f8
Create Date: 2024-10-14 13:03:28.930003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1dd6fd0fed3'
down_revision: Union[str, None] = 'e707670ab1f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION notify_receipt_status_change()
    RETURNS trigger AS $$
    DECLARE
        payload TEXT;
    BEGIN
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            payload := NEW.id::text;
            PERFORM pg_notify('receipt_status_changed', payload);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER receipt_status_change_trigger
    AFTER UPDATE ON receipts
    FOR EACH ROW
    EXECUTE FUNCTION notify_receipt_status_change();
    """)


def downgrade() -> None:
    op.execute("""
    DROP TRIGGER IF EXISTS receipt_status_change_trigger ON receipts;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS notify_receipt_status_change();
    """)
