"""
Authentication Routes - Login, Logout, Registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models.models import User, Role, Department
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
            # Set session
            session.permanent = True
            session['user_id'] = user.user_id
            session['full_name'] = user.full_name
            session['email'] = user.email
            session['role_id'] = user.role_id
            # Normalize and canonicalize role name for session and redirects
            role_raw = (user.role.role_name or '').strip().lower()
            display_map = {
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
    
    return render_template('auth/login.html')


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

            try:
                send_email(user.email, subject, body)
            except Exception:
                if os.getenv('FLASK_DEBUG', '0') == '1':
                    flash(f"Reset link (dev): {reset_url}", 'info')
                else:
                    flash('Unable to send reset email right now. Please contact the administrator.', 'error')
                return redirect(url_for('auth.forgot_password'))

        flash('If an account matches, a reset link has been sent to the email address.', 'success')
        return redirect(url_for('auth.login'))

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
