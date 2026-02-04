"""Truncate event-related tables and remove generated certificate files.
Use with care: this is destructive.
Run:
    source venv/bin/activate
    python3 tools/truncate_events.py
"""
import pymysql
import os
from datetime import datetime

# DB config (match app.py credentials)
DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER='root'
DB_PASS='Root1234!'
DB_NAME='campus_event_db'

CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'certificates')

print('Truncate script started at', datetime.now())

conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME, autocommit=False)
try:
    with conn.cursor() as cur:
        # Show counts before
        print('Counts before:')
        for t in ['certificates','attendance','registrations','approvals','feedback','events']:
            cur.execute(f'SELECT COUNT(*) AS cnt FROM `{t}`')
            print(f'  {t}:', cur.fetchone()['cnt'])

        # Disable foreign key checks, truncate in safe order
        cur.execute('SET FOREIGN_KEY_CHECKS=0;')
        cur.execute('TRUNCATE TABLE certificates;')
        cur.execute('TRUNCATE TABLE attendance;')
        cur.execute('TRUNCATE TABLE registrations;')
        cur.execute('TRUNCATE TABLE approvals;')
        cur.execute('TRUNCATE TABLE feedback;')
        cur.execute('TRUNCATE TABLE events;')
        # Reset auto-increment where appropriate
        cur.execute("ALTER TABLE certificates AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE attendance AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE registrations AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE approvals AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE feedback AUTO_INCREMENT = 1;")
        cur.execute("ALTER TABLE events AUTO_INCREMENT = 1;")
        cur.execute('SET FOREIGN_KEY_CHECKS=1;')

        conn.commit()

    # Remove certificate files
    removed=0
    if os.path.isdir(CERT_DIR):
        for fname in os.listdir(CERT_DIR):
            path = os.path.join(CERT_DIR, fname)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    removed += 1
            except Exception:
                pass

    # Show counts after
    with conn.cursor() as cur:
        print('\nCounts after:')
        for t in ['certificates','attendance','registrations','approvals','feedback','events']:
            cur.execute(f'SELECT COUNT(*) AS cnt FROM `{t}`')
            print(f'  {t}:', cur.fetchone()['cnt'])

    print(f'Files removed from {CERT_DIR}:', removed)
    print('Truncate completed at', datetime.now())
finally:
    conn.close()
