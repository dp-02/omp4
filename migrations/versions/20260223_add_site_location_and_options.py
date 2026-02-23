"""add site latitude, longitude, installation_mode, installation_env, power_structure

Revision ID: 20260223_ll
Revises: 20260223_tc
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = '20260223_ll'
down_revision = '20260223_tc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('installation_mode', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('installation_env', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('power_structure', sa.String(64), nullable=True))


def downgrade():
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.drop_column('power_structure')
        batch_op.drop_column('installation_env')
        batch_op.drop_column('installation_mode')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
