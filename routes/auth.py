"""
Authentication Routes - Login, Logout, Registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models.models import User, Role, Department, AppConfig, GuestOTP
from models import db
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from utils.email_utils import send_email
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or request.form.get('email') or '').strip()
        password = request.form.get('password')
        
        # Find user: students by username, others by email
        user = None
        user_by_username = User.query.filter_by(username=identifier).first() if identifier else None
        if user_by_username:
            role_name = (user_by_username.role.role_name or '').lower() if user_by_username.role else ''
            if role_name == 'student':
                user = user_by_username
            else:
                flash('Non-students must login with email.', 'error')
                return redirect(url_for('auth.login'))

        if not user:
            user_by_email = User.query.filter_by(email=identifier).first() if identifier else None
            if user_by_email:
                role_name = (user_by_email.role.role_name or '').lower() if user_by_email.role else ''
                if role_name == 'student' and user_by_email.username:
                    flash('Students must login using username.', 'error')
                    return redirect(url_for('auth.login'))
                user = user_by_email

        if user and user.check_password(password):
            # If this is a guest user, block login when expired/archived.
            # Do not affect other roles.
            from datetime import datetime as _dt
            role_name_db = (user.role.role_name or '').strip().lower() if user.role else ''
            is_guest_user = role_name_db == 'guest' or bool(getattr(user, 'is_guest', False))
            if is_guest_user:
                # If expiry_date set and in the past, mark expired and prevent login
                if getattr(user, 'expiry_date', None) and user.expiry_date and _dt.utcnow() > user.expiry_date:
                    try:
                        user.guest_status = 'expired'
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    flash('Guest account expired. Please request a new guest account.', 'error')
                    return redirect(url_for('auth.login'))

            # Set session
            session.permanent = True
            session['user_id'] = user.user_id
            session['full_name'] = user.full_name
            session['email'] = user.email
            session['role_id'] = user.role_id
            # Normalize and canonicalize role name for session and redirects
            role_raw = (user.role.role_name or '').strip().lower()
            display_map = {
                'guest': 'Guest',
                'student': 'Student',
                'event organizer': 'Event Organizer',
                'organizer': 'Event Organizer',
                'hod': 'HOD',
                'principal': 'Principal',
                'admin': 'Admin'
            }
            session['role_name'] = display_map.get(role_raw, (user.role.role_name or '').title())
            session['dept_id'] = user.dept_id

            # Redirect based on normalized role
            if role_raw == 'student':
                return redirect(url_for('student.dashboard'))
            elif role_raw in ('event organizer', 'organizer'):
                return redirect(url_for('organizer.dashboard'))
            elif role_raw == 'hod':
                return redirect(url_for('hod.dashboard'))
            elif role_raw == 'principal':
                return redirect(url_for('principal.dashboard'))
            elif role_raw == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    guest_enabled = AppConfig.query.get('guest_enabled')
    return render_template('auth/login.html', guest_enabled=guest_enabled)



    # --- Guest login flow (mobile OTP only) ---
from datetime import datetime, timedelta
import random

@bp.route('/guest', methods=['GET', 'POST'])
def guest_request():
    """Guest login using mobile number only: send OTP and redirect to verify."""
    cfg = AppConfig.query.get('guest_enabled')
    if not cfg or cfg.value != '1':
        flash('Guest login is disabled', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        mobile = (request.form.get('mobile') or '').strip()
        if not mobile or not mobile.replace('+', '').isdigit():
            flash('Please provide a valid mobile number', 'error')
            return redirect(url_for('auth.guest_request'))

        # Rate limiting: max 5 OTPs in last hour
        recent = GuestOTP.query.filter(GuestOTP.mobile_number == mobile,
                                       GuestOTP.created_at >= datetime.utcnow() - timedelta(hours=1)).count()
        if recent >= 5:
            flash('Too many OTP requests. Try again later.', 'error')
            return redirect(url_for('auth.login'))

        code = f"{random.randint(100000, 999999)}"
        otp = GuestOTP(mobile_number=mobile, code=code)
        db.session.add(otp)
        db.session.commit()

        # Send SMS via configured provider (Twilio) with graceful fallback
        sent = False
        try:
            from utils.sms_utils import send_sms
            sent = send_sms(mobile, f"Your Campus Events OTP is: {code}")
        except Exception:
            sent = False

        # Development fallback: show OTP in flash if SMS not sent and debugging enabled
        if not sent and os.getenv('FLASK_DEBUG', '0') == '1':
            flash(f'Guest OTP (dev): {code}', 'info')

        return redirect(url_for('auth.guest_verify', mobile=mobile))

    return render_template('auth/guest_request.html')


@bp.route('/guest/verify', methods=['GET', 'POST'])
def guest_verify():
    """Verify OTP sent to mobile and create/login guest user."""
    mobile = (request.args.get('mobile') or request.form.get('mobile') or '').strip()
    if not mobile:
        flash('Mobile number required', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        otp = GuestOTP.query.filter_by(mobile_number=mobile, code=code, used=False).order_by(GuestOTP.created_at.desc()).first()
        if not otp or (datetime.utcnow() - otp.created_at).total_seconds() > 300:
            flash('Invalid or expired OTP', 'error')
            return redirect(url_for('auth.guest_request'))

        otp.used = True
        db.session.commit()

        # Prefer users with this mobile who have the Guest role, otherwise match by mobile number
        user = User.query.filter_by(mobile_number=mobile).first()
        if user:
            role_name_db = (user.role.role_name or '').strip().lower() if user.role else ''
            if role_name_db != 'guest' and not getattr(user, 'is_guest', False):
                # existing non-guest user with same mobile — treat as no match
                user = None
        # Prefer a dedicated 'Guest' role; fall back to 'Student' if not present
        guest_role = Role.query.filter(Role.role_name.ilike('guest')).first()
        # Ensure a dedicated Guest role exists; create if missing
        if not guest_role:
            try:
                guest_role = Role(role_name='Guest')
                db.session.add(guest_role)
                db.session.commit()
            except Exception:
                db.session.rollback()
                guest_role = None
        student_role = Role.query.filter(Role.role_name.ilike('student')).first()
        if not user:
            validity_days = 30
            vcfg = AppConfig.query.get('guest_validity_days')
            if vcfg and vcfg.value and vcfg.value.isdigit():
                validity_days = int(vcfg.value)
            expiry = datetime.utcnow() + timedelta(days=validity_days)
            assigned_role_id = None
            if guest_role:
                assigned_role_id = guest_role.role_id
            elif student_role:
                assigned_role_id = student_role.role_id
            else:
                assigned_role_id = 1

            user = User(
                full_name=f'Guest {mobile[-4:]}',
                username=None,
                email=None,
                role_id=assigned_role_id,
                dept_id=None
            )
            user.set_password(__import__('uuid').uuid4().hex)
            # Rely on role assignment for guest semantics; legacy `is_guest` column left as-is
            user.mobile_number = mobile
            # generate a short unique guest identifier and store it in `username`
            import uuid
            def make_code():
                return f"G-{uuid.uuid4().hex[:8].upper()}"
            code = make_code()
            # ensure uniqueness among usernames
            from models.models import User as _U
            while _U.query.filter_by(username=code).first():
                code = make_code()
            user.username = code
            # also store the guest identifier in `username` so it can be used as Guest ID
            user.username = code
            user.expiry_date = expiry
            user.guest_status = 'active'
            db.session.add(user)
            db.session.commit()
        else:
            # ensure existing guest user has a username we can use as Guest ID
            if not user.username:
                import uuid
                def make_code():
                    return f"G-{uuid.uuid4().hex[:8].upper()}"
                code = make_code()
                from models.models import User as _U
                while _U.query.filter_by(username=code).first():
                    code = make_code()
                user.username = code
                db.session.commit()
            if user.expiry_date and datetime.utcnow() > user.expiry_date:
                user.guest_status = 'expired'
                db.session.commit()
                flash('Guest account expired. Please request a new guest account.', 'error')
                return redirect(url_for('auth.login'))

        session.permanent = True
        session['user_id'] = user.user_id
        session['full_name'] = user.full_name
        # For guest users prefer mobile_number; email may be None
        session['email'] = user.email
        session['role_id'] = user.role_id
        # Use Guest as display role for guest logins
        session['role_name'] = 'Guest'
        session['dept_id'] = user.dept_id
        # Backwards-compatible session flag
        session['is_guest'] = (user.role and (user.role.role_name or '').strip().lower() == 'guest') or bool(getattr(user, 'is_guest', False))
        session['mobile_number'] = user.mobile_number
        # store guest identifier in session (username acts as Guest ID)
        session['guest_code'] = user.username
        session['username'] = user.username
        return redirect(url_for('student.dashboard'))

    return render_template('auth/guest_verify.html', mobile=mobile)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if session.get('role_name', '').lower() != 'admin':
        flash('Registration is disabled. Please contact the administrator.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = (request.form.get('username') or '').strip()
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role_id = request.form.get('role_id')
        dept_id = request.form.get('dept_id')
        
        # Validation
        if len(password or '') < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))

        if username and User.query.filter_by(username=username).first():
            flash('Username already registered', 'error')
            return redirect(url_for('auth.register'))
        
        # Create user
        user = User(
            full_name=full_name,
            username=username or None,
            email=email,
            role_id=int(role_id),
            dept_id=int(dept_id) if dept_id else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    # Get roles and departments for form
    roles = Role.query.all()
    departments = Department.query.all()
    
    return render_template('auth/register.html', roles=roles, departments=departments)


@bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup disabled — redirect to login."""
    flash('Registration is disabled. Please contact the administrator.', 'warning')
    return redirect(url_for('auth.login'))

@bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change password for logged-in users"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    # Prevent guest users from using the change-password feature
    if session.get('is_guest') or (session.get('role_name') or '').strip().lower() == 'guest':
        flash('Guest accounts cannot change password.', 'warning')
        return redirect(url_for('common.profile'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.query.get(session['user_id'])
        
        if not user or not user.check_password(old_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/change_password.html')


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request a password reset link"""
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or request.form.get('email') or '').strip()

        user = None
        if identifier:
            user = User.query.filter_by(email=identifier).first()
            if not user:
                user = User.query.filter_by(username=identifier).first()

        # Always show the same response to prevent user enumeration
        if user:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps({'user_id': user.user_id}, salt='password-reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            subject = 'Reset your Campus Events password'
            body = (
                f"Hello {user.full_name},\n\n"
                "We received a request to reset your password. "
                "Use the link below to set a new password (valid for 60 minutes):\n\n"
                f"{reset_url}\n\n"
                "If you didn't request this, you can ignore this email."
            )
            
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using a token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt='password-reset', max_age=3600)
        user_id = data.get('user_id')
    except SignatureExpired:
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Invalid reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(user_id)
    if not user:
        flash('Invalid reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if len(new_password or '') < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        user.set_password(new_password)
        db.session.commit()
        flash('Password reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
