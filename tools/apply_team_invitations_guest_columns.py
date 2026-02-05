#!/usr/bin/env python3
"""
Apply non-destructive guest columns to `team_invitations` table.
Run: python tools/apply_team_invitations_guest_columns.py
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
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'team_invitations' AND COLUMN_NAME = :col
        """)
        return int(conn.execute(q, {'col': col}).scalar()) > 0

    changes = [
        ("is_guest", "ALTER TABLE team_invitations ADD COLUMN is_guest TINYINT(1) NOT NULL DEFAULT 0"),
        ("mobile_number", "ALTER TABLE team_invitations ADD COLUMN mobile_number VARCHAR(64) DEFAULT NULL"),
        ("expiry_date", "ALTER TABLE team_invitations ADD COLUMN expiry_date DATETIME DEFAULT NULL"),
        ("guest_status", "ALTER TABLE team_invitations ADD COLUMN guest_status VARCHAR(32) DEFAULT 'active'"),
    ]

    for col, sql in changes:
        if not col_exists(col):
            print(f"Adding team_invitations.{col} ...")
            try:
                conn.execute(text(sql))
                print('  OK')
            except Exception as e:
                print('  FAILED:', e)
                db.session.rollback()
        else:
            print(f"team_invitations.{col} exists, skipping.")

    # ensure non-unique index on team_invitations.mobile_number if absent
    idx_check = text("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'team_invitations' AND COLUMN_NAME = 'mobile_number'
    """)
    if int(conn.execute(idx_check).scalar()) == 0:
        try:
            conn.execute(text("CREATE INDEX idx_team_invitations_mobile ON team_invitations (mobile_number);"))
            print('Created index idx_team_invitations_mobile')
        except Exception as e:
            print('Failed to create index on team_invitations.mobile_number:', e)
            db.session.rollback()
    else:
        print('Index on team_invitations.mobile_number exists, skipping.')

    db.session.commit()
    print('team_invitations guest columns applied.')
