#!/usr/bin/env python3
"""
Apply non-destructive guest columns to `certificate_templates` table.
Run: python tools/apply_certificate_templates_guest_columns.py
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
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'certificate_templates' AND COLUMN_NAME = :col
        """)
        return int(conn.execute(q, {'col': col}).scalar()) > 0

    changes = [
        ("is_guest", "ALTER TABLE certificate_templates ADD COLUMN is_guest TINYINT(1) NOT NULL DEFAULT 0"),
        ("mobile_number", "ALTER TABLE certificate_templates ADD COLUMN mobile_number VARCHAR(64) DEFAULT NULL"),
        ("expiry_date", "ALTER TABLE certificate_templates ADD COLUMN expiry_date DATETIME DEFAULT NULL"),
        ("guest_status", "ALTER TABLE certificate_templates ADD COLUMN guest_status VARCHAR(32) DEFAULT 'active'"),
    ]

    for col, sql in changes:
        if not col_exists(col):
            print(f"Adding certificate_templates.{col} ...")
            try:
                conn.execute(text(sql))
                print('  OK')
            except Exception as e:
                print('  FAILED:', e)
                db.session.rollback()
        else:
            print(f"certificate_templates.{col} exists, skipping.")

    # ensure non-unique index on certificate_templates.mobile_number if absent
    idx_check = text("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'certificate_templates' AND COLUMN_NAME = 'mobile_number'
    """)
    if int(conn.execute(idx_check).scalar()) == 0:
        try:
            conn.execute(text("CREATE INDEX idx_certificate_templates_mobile ON certificate_templates (mobile_number);"))
            print('Created index idx_certificate_templates_mobile')
        except Exception as e:
            print('Failed to create index on certificate_templates.mobile_number:', e)
            db.session.rollback()
    else:
        print('Index on certificate_templates.mobile_number exists, skipping.')

    db.session.commit()
    print('certificate_templates guest columns applied.')
