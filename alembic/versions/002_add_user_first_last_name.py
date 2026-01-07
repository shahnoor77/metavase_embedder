"""add first_name and last_name to users

Revision ID: 002
Revises: 001
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # No-op: fields already created in initial schema
    pass


def downgrade():
    # No-op
    pass

