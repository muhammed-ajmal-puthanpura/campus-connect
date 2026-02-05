"""add guest schema

Revision ID: 0001_add_guest_schema
Revises: 
Create Date: 2026-02-05 21:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_guest_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add non-destructive columns to users
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest TINYINT(1) NOT NULL DEFAULT 0;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(64) DEFAULT NULL;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS expiry_date DATETIME DEFAULT NULL;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS guest_status VARCHAR(32) DEFAULT 'active';")

    # Create guest_otps table if missing
    op.execute('''
    CREATE TABLE IF NOT EXISTS guest_otps (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      mobile_number VARCHAR(64) NOT NULL,
      code VARCHAR(16) NOT NULL,
      used TINYINT(1) NOT NULL DEFAULT 0,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      INDEX (mobile_number),
      INDEX (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # Create app_config table if missing
    op.execute('''
    CREATE TABLE IF NOT EXISTS app_config (
      id INT AUTO_INCREMENT PRIMARY KEY,
      `key` VARCHAR(128) NOT NULL,
      `value` TEXT,
      UNIQUE KEY ux_appconfig_key (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # Add index on users.mobile_number if absent
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_mobile ON users (mobile_number);")


def downgrade():
    # Downgrade intentionally left as NO-OP to avoid destructive drops in production.
    print('Downgrade skipped to avoid dropping columns/tables in production environment.')
