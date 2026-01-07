"""add is_active and timestamps to users

Revision ID: 003
Revises: 002
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
  # Add columns if they don't already exist.
  # Using raw SQL for IF NOT EXISTS support.
  op.execute(
    """
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'is_active'
      ) THEN
        ALTER TABLE users
          ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'created_at'
      ) THEN
        ALTER TABLE users
          ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT NOW();
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'updated_at'
      ) THEN
        ALTER TABLE users
          ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT NOW();
      END IF;
    END;
    $$;
    """
  )


def downgrade() -> None:
  # Safe to drop; will error if columns used elsewhere, but matches our model rollback.
  op.execute(
    """
    ALTER TABLE users
      DROP COLUMN IF EXISTS updated_at,
      DROP COLUMN IF EXISTS created_at,
      DROP COLUMN IF EXISTS is_active;
    """
  )


