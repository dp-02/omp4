"""add site greenpower_rate and site_phase taipower_rate

Revision ID: 20260202_rate
Revises: 1016ca09b393
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260202_rate'
down_revision = '1016ca09b393'
branch_labels = None
depends_on = None


def upgrade():
    # 新增 site.greenpower_rate、site_phase.taipower_rate
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.add_column(sa.Column('greenpower_rate', sa.Integer(), nullable=True))
    with op.batch_alter_table('site_phase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('taipower_rate', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('site_phase', schema=None) as batch_op:
        batch_op.drop_column('taipower_rate')
    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.drop_column('greenpower_rate')
