#!/usr/bin/env python3
from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    try:
        print('Altering users.email to be NULLABLE...')
        db.session.execute(text("ALTER TABLE users MODIFY COLUMN email VARCHAR(120) NULL;"))
        db.session.commit()
        print('Done.')
    except Exception as e:
        print('Failed to alter email column:', e)
        db.session.rollback()
        raise
