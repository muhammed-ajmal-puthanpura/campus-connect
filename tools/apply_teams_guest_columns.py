#!/usr/bin/env python3
"""
Apply non-destructive guest columns to `teams` table.
Run: python tools/apply_teams_guest_columns.py
"""
import sys
from sqlalchemy import text
try:
    from app import app
    from models import db
except Exception as e:
    print('Failed to import app or db:', e)
    sys.exit(2)

with app.app_context():
    conn = db.session.connection()
    def col_exists(col):
        q = text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teams' AND COLUMN_NAME = :col
        """)
        return int(conn.execute(q, {'col': col}).scalar()) > 0

    changes = [
        ("is_guest", "ALTER TABLE teams ADD COLUMN is_guest TINYINT(1) NOT NULL DEFAULT 0"),
        ("mobile_number", "ALTER TABLE teams ADD COLUMN mobile_number VARCHAR(64) DEFAULT NULL"),
        ("expiry_date", "ALTER TABLE teams ADD COLUMN expiry_date DATETIME DEFAULT NULL"),
        ("guest_status", "ALTER TABLE teams ADD COLUMN guest_status VARCHAR(32) DEFAULT 'active'"),
    ]

    for col, sql in changes:
        if not col_exists(col):
            print(f"Adding teams.{col} ...")
            try:
                conn.execute(text(sql))
                print('  OK')
            except Exception as e:
                print('  FAILED:', e)
                db.session.rollback()
        else:
            print(f"teams.{col} exists, skipping.")

    # ensure index on teams.mobile_number if absent
    idx_check = text("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teams' AND COLUMN_NAME = 'mobile_number'
    """)
    if int(conn.execute(idx_check).scalar()) == 0:
        try:
            conn.execute(text("CREATE INDEX idx_teams_mobile ON teams (mobile_number);"))
            print('Created index idx_teams_mobile')
        except Exception as e:
            print('Failed to create index on teams.mobile_number:', e)
            db.session.rollback()
    else:
        print('Index on teams.mobile_number exists, skipping.')

    db.session.commit()
    print('teams guest columns applied.')
