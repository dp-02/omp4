"""add site total_capacity (總裝置容量)

Revision ID: 20260223_tc
Revises: 20260223_gp
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = '20260223_tc'
down_revision = '20260223_gp'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_capacity', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.drop_column('total_capacity')
