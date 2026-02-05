#!/usr/bin/env python3
"""
Apply guest schema changes safely using the app context and SQLAlchemy.
This script will:
 - add `is_guest`, `mobile_number`, `expiry_date`, `guest_status` to `users` if missing
 - create `guest_otps` and `app_config` tables if missing
 - add an index on `users.mobile_number` (non-unique)

Run from project root: python tools/apply_guest_schema.py
"""
import sys
from sqlalchemy import text

# Import the Flask app and db
try:
    from app import app
    from models import db
except Exception as e:
    print("Failed to import app or db:", e)
    sys.exit(2)

ALTERS = [
    ("is_guest", "ALTER TABLE users ADD COLUMN is_guest TINYINT(1) NOT NULL DEFAULT 0"),
    ("mobile_number", "ALTER TABLE users ADD COLUMN mobile_number VARCHAR(64) DEFAULT NULL"),
    ("expiry_date", "ALTER TABLE users ADD COLUMN expiry_date DATETIME DEFAULT NULL"),
    ("guest_status", "ALTER TABLE users ADD COLUMN guest_status VARCHAR(32) DEFAULT 'active'"),
]

GUEST_OTPS_SQL = '''
CREATE TABLE IF NOT EXISTS guest_otps (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  mobile_number VARCHAR(64) NOT NULL,
  code VARCHAR(16) NOT NULL,
  used TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (mobile_number),
  INDEX (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

APP_CONFIG_SQL = '''
CREATE TABLE IF NOT EXISTS app_config (
  id INT AUTO_INCREMENT PRIMARY KEY,
  `key` VARCHAR(128) NOT NULL,
  `value` TEXT,
  UNIQUE KEY ux_appconfig_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_users_mobile ON users (mobile_number);"
# MySQL doesn't support CREATE INDEX IF NOT EXISTS prior to 8.0. To be safe we'll check information_schema.


def column_exists(conn, table, column):
    q = text("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table AND COLUMN_NAME = :column
    """)
    return int(conn.execute(q, {"table": table, "column": column}).scalar()) > 0


def table_exists(conn, table):
    q = text("""
        SELECT COUNT(*) FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table
    """)
    return int(conn.execute(q, {"table": table}).scalar()) > 0


with app.app_context():
    conn = db.session.connection()
    try:
        # Add columns if missing
        for col, sql in ALTERS:
            if not column_exists(conn, 'users', col):
                print(f"Adding column users.{col} ...")
                try:
                    conn.execute(text(sql))
                    print("  OK")
                except Exception as e:
                    print(f"  FAILED to add {col}: {e}")
                    db.session.rollback()
            else:
                print(f"Column users.{col} already exists, skipping.")

        # Create guest_otps
        if not table_exists(conn, 'guest_otps'):
            print("Creating table guest_otps...")
            conn.execute(text(GUEST_OTPS_SQL))
            print("  OK")
        else:
            print("Table guest_otps exists, skipping.")

        # Create app_config
        if not table_exists(conn, 'app_config'):
            print("Creating table app_config...")
            conn.execute(text(APP_CONFIG_SQL))
            print("  OK")
        else:
            print("Table app_config exists, skipping.")

        # Ensure index on mobile_number (non-unique)
        idx_check = text("""
            SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'mobile_number'
        """)
        if int(conn.execute(idx_check).scalar()) == 0:
            print("Creating index on users.mobile_number...")
            try:
                conn.execute(text("CREATE INDEX idx_users_mobile ON users (mobile_number);"))
                print("  OK")
            except Exception as e:
                print("  FAILED to create index:", e)
                db.session.rollback()
        else:
            print("Index on users.mobile_number exists, skipping.")

        db.session.commit()
        print("Schema changes applied successfully.")
    except Exception as e:
        print("Error while applying schema:", e)
        db.session.rollback()
        sys.exit(1)

    # Note: we intentionally do NOT add a UNIQUE constraint on mobile_number here.
    # If you want a UNIQUE index, please ensure there are no duplicate mobile_number values first.

    # Print next steps
    print("\nNext steps:")
    print(" - Optional: verify duplicate mobile numbers before adding UNIQUE index:")
    print("   SELECT mobile_number, COUNT(*) c FROM users WHERE mobile_number IS NOT NULL GROUP BY mobile_number HAVING c > 1;")
    print(" - Run python tools/init_guest_config.py to ensure app_config keys exist.")

