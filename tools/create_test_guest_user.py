#!/usr/bin/env python3
from app import app
from models.models import User, Role
from models import db
from datetime import datetime, timedelta

MOBILE = '+916282153391'

with app.app_context():
    user = User.query.filter_by(mobile_number=MOBILE, is_guest=True).first()
    if user:
        print('User already exists:', user.user_id, user.full_name, user.email)
    else:
        student_role = Role.query.filter(Role.role_name.ilike('student')).first()
        role_id = student_role.role_id if student_role else 1
        expiry = datetime.utcnow() + timedelta(days=30)
        u = User(full_name=f'Guest {MOBILE[-4:]}', username=None, email=None, role_id=role_id, dept_id=None)
        u.set_password('temporary')
        u.is_guest = True
        u.mobile_number = MOBILE
        u.expiry_date = expiry
        u.guest_status = 'active'
        db.session.add(u)
        db.session.commit()
        print('Created guest user:', u.user_id, u.full_name, u.mobile_number)
