"""Add rejection_note

Revision ID: add_rejection_note
Revises: 
Create Date: 2025-11-28 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rejection_note'
down_revision = None  # Update this to the most recent migration ID if there are existing migrations
branch_labels = None
depends_on = None


def upgrade():
    # Add rejection_note column to transaction table
    op.add_column('transaction', sa.Column('rejection_note', sa.String(length=500), nullable=True))


def downgrade():
    # Remove rejection_note column from transaction table
    op.drop_column('transaction', 'rejection_note')
