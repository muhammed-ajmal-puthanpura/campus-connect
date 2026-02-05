#!/usr/bin/env python3
from app import app
from models.models import GuestOTP
from models import db

MOBILE = '+916282153391'

with app.app_context():
    otp = GuestOTP.query.filter_by(mobile_number=MOBILE).order_by(GuestOTP.created_at.desc()).first()
    if otp:
        print('OTP found:', otp.code, 'used=', otp.used, 'created_at=', otp.created_at)
    else:
        print('No OTP found for', MOBILE)
