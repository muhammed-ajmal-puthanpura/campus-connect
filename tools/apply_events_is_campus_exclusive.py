#!/usr/bin/env python3
"""
Add `is_campus_exclusive` column to `events` table if missing (idempotent).
Run: python tools/apply_events_is_campus_exclusive.py
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
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = :col
        """)
        return int(conn.execute(q, {'col': col}).scalar()) > 0

    col = 'is_campus_exclusive'
    sql = "ALTER TABLE events ADD COLUMN is_campus_exclusive TINYINT(1) NOT NULL DEFAULT 0"
    if not col_exists(col):
        print(f"Adding events.{col} ...")
        try:
            conn.execute(text(sql))
            print('  OK')
        except Exception as e:
            print('  FAILED:', e)
            db.session.rollback()
    else:
        print(f"events.{col} exists, skipping.")

    db.session.commit()
    print('events.is_campus_exclusive applied.')
