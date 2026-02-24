"""add site_phase_inverter_sld table (SitePhaseInverterSld)

Revision ID: 20260224_sld
Revises: 20260223_ll
Create Date: 2026-02-24

"""
from alembic import op
import sqlalchemy as sa


revision = '20260224_sld'
down_revision = '20260223_ll'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'site_phase_inverter_sld',
        sa.Column('uid', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('inverter_uid', sa.Integer(), nullable=False),
        sa.Column('inv', sa.String(256), nullable=True),
        sa.Column('mppt', sa.String(256), nullable=True),
        sa.Column('string', sa.String(256), nullable=True),
        sa.Column('orientation', sa.String(64), nullable=True),
        sa.Column('tilt_angle', sa.Float(), nullable=True),
        sa.Column('module_wattage', sa.Float(), nullable=True),
        sa.Column('module_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['inverter_uid'], ['site_phase_inverter.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('uid'),
    )


def downgrade():
    op.drop_table('site_phase_inverter_sld')
