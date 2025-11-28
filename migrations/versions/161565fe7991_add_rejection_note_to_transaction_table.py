"""Add rejection_note to transaction table

Revision ID: 161565fe7991
Revises: f6bfcecbb709
Create Date: 2025-11-28 22:19:05.275693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '161565fe7991'
down_revision = 'f6bfcecbb709'
branch_labels = None
depends_on = None


def upgrade():
    # Add rejection_note column with proper constraints
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('rejection_note', sa.String(length=500), nullable=True)
        )


def downgrade():
    # Remove rejection_note column
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('rejection_note')
