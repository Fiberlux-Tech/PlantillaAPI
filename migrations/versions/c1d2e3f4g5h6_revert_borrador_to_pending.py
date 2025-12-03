"""Revert BORRADOR status to PENDING for all transactions

Revision ID: c1d2e3f4g5h6
Revises: 78e08d189b9d
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = '78e08d189b9d'
branch_labels = None
depends_on = None


def upgrade():
    # Update all BORRADOR transactions to PENDING status
    op.execute(
        """
        UPDATE transaction
        SET "ApprovalStatus" = 'PENDING'
        WHERE "ApprovalStatus" = 'BORRADOR';
        """
    )


def downgrade():
    # Optionally revert PENDING back to BORRADOR (not recommended)
    # This is provided for completeness but should rarely be used
    pass
