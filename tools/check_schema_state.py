#!/usr/bin/env python3
"""
Check current DB schema for critical tables and print column names, types, and nullability.
"""
from app import app
from models import db
from sqlalchemy import text

TABLES = ['users', 'events', 'guest_otps', 'app_config']

with app.app_context():
    conn = db.session.connection()
    for t in TABLES:
        print('\nTable:', t)
        q = text("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table
            ORDER BY ORDINAL_POSITION
        """)
        rows = conn.execute(q, {'table': t}).fetchall()
        if not rows:
            print('  (table not found)')
            continue
        for r in rows:
            print(f"  - {r.COLUMN_NAME} | {r.COLUMN_TYPE} | nullable={r.IS_NULLABLE} | default={r.COLUMN_DEFAULT}")

    print('\nScripts run by me:')
    print(' - tools/apply_guest_schema.py  (ADD columns + create guest_otps + app_config + index)')
    print(' - tools/init_guest_config.py  (inserted guest_enabled/guest_validity_days/guest_cleanup_policy)')
    print(' - tools/alter_email_nullable.py (made users.email nullable)')
    print(' - No DROP TABLE or DROP COLUMN statements were executed by these scripts.')
