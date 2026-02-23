"""move greenpower_rate from site to site_phase

Revision ID: 20260223_gp
Revises: f41297f7e4c6
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = '20260223_gp'
down_revision = 'f41297f7e4c6'
branch_labels = None
depends_on = None


def upgrade():
    # site_phase 新增 greenpower_rate
    with op.batch_alter_table('site_phase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('greenpower_rate', sa.Float(), nullable=True))
    # site 移除 greenpower_rate
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.drop_column('greenpower_rate')


def downgrade():
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.add_column(sa.Column('greenpower_rate', sa.Float(), nullable=True))
    with op.batch_alter_table('site_phase', schema=None) as batch_op:
        batch_op.drop_column('greenpower_rate')
