"""Refactor currency architecture complete

Revision ID: 78e08d189b9d
Revises: 161565fe7991
Create Date: 2025-12-01 22:07:54.454655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78e08d189b9d'
down_revision = '161565fe7991'
branch_labels = None
depends_on = None


def upgrade():
    # Transaction table changes
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        # Rename existing fields to _original pattern
        batch_op.alter_column('MRC', new_column_name='MRC_original')
        batch_op.alter_column('mrc_currency', new_column_name='MRC_currency')
        batch_op.alter_column('NRC', new_column_name='NRC_original')
        batch_op.alter_column('nrc_currency', new_column_name='NRC_currency')

        # Add _pen fields
        batch_op.add_column(sa.Column('MRC_pen', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('NRC_pen', sa.Float(), nullable=False, server_default='0.0'))

    # FixedCost table changes
    with op.batch_alter_table('fixed_cost', schema=None) as batch_op:
        # Rename existing fields
        batch_op.alter_column('costoUnitario', new_column_name='costoUnitario_original')
        batch_op.alter_column('costo_currency', new_column_name='costoUnitario_currency')

        # Add _pen field
        batch_op.add_column(sa.Column('costoUnitario_pen', sa.Float(), nullable=False, server_default='0.0'))

    # RecurringService table changes
    with op.batch_alter_table('recurring_service', schema=None) as batch_op:
        # Rename existing fields
        batch_op.alter_column('P', new_column_name='P_original')
        batch_op.alter_column('CU1', new_column_name='CU1_original')
        batch_op.alter_column('CU2', new_column_name='CU2_original')
        batch_op.alter_column('cu_currency', new_column_name='CU_currency')

        # Add new fields
        batch_op.add_column(sa.Column('P_currency', sa.String(length=3), nullable=False, server_default='PEN'))
        batch_op.add_column(sa.Column('P_pen', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('CU1_pen', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('CU2_pen', sa.Float(), nullable=False, server_default='0.0'))


def downgrade():
    # RecurringService table rollback
    with op.batch_alter_table('recurring_service', schema=None) as batch_op:
        batch_op.drop_column('CU2_pen')
        batch_op.drop_column('CU1_pen')
        batch_op.drop_column('P_pen')
        batch_op.drop_column('P_currency')

        batch_op.alter_column('CU_currency', new_column_name='cu_currency')
        batch_op.alter_column('CU2_original', new_column_name='CU2')
        batch_op.alter_column('CU1_original', new_column_name='CU1')
        batch_op.alter_column('P_original', new_column_name='P')

    # FixedCost table rollback
    with op.batch_alter_table('fixed_cost', schema=None) as batch_op:
        batch_op.drop_column('costoUnitario_pen')

        batch_op.alter_column('costoUnitario_currency', new_column_name='costo_currency')
        batch_op.alter_column('costoUnitario_original', new_column_name='costoUnitario')

    # Transaction table rollback
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('NRC_pen')
        batch_op.drop_column('MRC_pen')

        batch_op.alter_column('NRC_currency', new_column_name='nrc_currency')
        batch_op.alter_column('NRC_original', new_column_name='NRC')
        batch_op.alter_column('MRC_currency', new_column_name='mrc_currency')
        batch_op.alter_column('MRC_original', new_column_name='MRC')
