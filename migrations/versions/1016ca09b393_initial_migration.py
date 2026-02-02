"""Initial migration

Revision ID: 1016ca09b393
Revises: 
Create Date: 2026-02-02 16:45:01.652761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1016ca09b393'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 案場與期數費率欄位已移至 20260202_add_site_phase_rate_columns
    pass


def downgrade():
    pass
