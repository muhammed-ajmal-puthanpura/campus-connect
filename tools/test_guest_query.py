#!/usr/bin/env python3
from app import app
from models.models import User, Role
from models import db

MOBILE = '+916282153391'

with app.app_context():
    u = User.query.filter_by(mobile_number=MOBILE).join(Role).filter(Role.role_name.ilike('guest')).first()
    if u:
        role_name = u.role.role_name if u.role else '—'
        print('Found guest user:', u.user_id, u.full_name, u.mobile_number, role_name)
    else:
        print('No guest user found for', MOBILE)
