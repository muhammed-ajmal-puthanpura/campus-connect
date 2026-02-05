"""
Idempotent script to add `guest_code` column to `users` table.
Run with: PYTHONPATH=. python tools/apply_guest_code_column.py
This will only ALTER the table if the column is missing.
"""
from sqlalchemy import text
from models import db

conn = db.engine.connect()
try:
    # Check information_schema for column presence
    res = conn.execute(text("""
        SELECT COUNT(*) cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'guest_code'
    """))
    cnt = res.scalar()
    if cnt and int(cnt) > 0:
        print('Column users.guest_code already exists — nothing to do.')
    else:
        print('Adding column users.guest_code (VARCHAR(32) NULL) ...')
        conn.execute(text("ALTER TABLE users ADD COLUMN guest_code VARCHAR(32) DEFAULT NULL;"))
        print('Column added.')
        # Create a non-unique index to speed lookups (do NOT create UNIQUE here to avoid failing on duplicates)
        print('Creating index idx_users_guest_code if absent...')
        try:
            conn.execute(text("CREATE INDEX idx_users_guest_code ON users (guest_code);"))
            print('Index created.')
        except Exception as e:
            # MySQL will error if index exists; catch and print
            print('Index creation failed or already exists:', e)
        print('DONE: users.guest_code added. Consider creating UNIQUE constraint after deduplication if desired.')
finally:
    conn.close()
