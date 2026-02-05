"""
Common Routes - Shared functionality across roles
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, abort
from models import db

bp = Blueprint('common', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """View user profile"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from models.models import User
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        mobile = (request.form.get('mobile_number') or '').strip()

        role_name = (user.role.role_name or '').lower() if user.role else ''
        # Determine guest status primarily from role; fall back to legacy `is_guest` flag
        is_guest_user = (user.role and (user.role.role_name or '').strip().lower() == 'guest') or bool(getattr(user, 'is_guest', False))
        # Treat real students (non-guest) as locked for name/username edits.
        is_student = (role_name == 'student') and not is_guest_user

        # For guest users, require mobile number instead of email
        if is_guest_user:
            if not mobile or not mobile.replace('+', '').isdigit():
                flash('Mobile number is required for guest accounts.', 'error')
                return redirect(url_for('common.profile'))
        else:
            if not email:
                flash('Email is required.', 'error')
                return redirect(url_for('common.profile'))

        # Allow editing name for non-students. Do NOT allow username changes for guest users.
        if not is_student:
            if not full_name:
                flash('Name is required.', 'error')
                return redirect(url_for('common.profile'))

            # Only allow username changes for non-guest, non-student users and not for admin/hod/principal
            if username and username != user.username and not is_guest_user and role_name not in ('admin', 'hod', 'principal', 'organizer', 'event organizer'):
                if User.query.filter_by(username=username).first():
                    flash('Username already in use. Please choose another.', 'error')
                    return redirect(url_for('common.profile'))
                user.username = username

            if full_name != user.full_name:
                user.full_name = full_name
                session['full_name'] = full_name

        # Update mobile for guest users
        if is_guest_user:
            if mobile != (user.mobile_number or ''):
                # ensure uniqueness among users for this mobile (excluding this user)
                existing = User.query.filter(User.mobile_number == mobile, User.user_id != user.user_id).first()
                if existing:
                    flash('Mobile number already in use. Please choose another.', 'error')
                    return redirect(url_for('common.profile'))
                user.mobile_number = mobile
                session['mobile_number'] = mobile
        else:
            if email != (user.email or ''):
                if User.query.filter_by(email=email).first():
                    flash('Email already in use. Please choose another.', 'error')
                    return redirect(url_for('common.profile'))
                user.email = email
                session['email'] = email

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('common.profile'))
    
    return render_template('common/profile.html', user=user)



@bp.route('/session-info')
def session_info():
    """Debug route: return current session contents (requires login)."""
    if not current_app.debug:
        abort(404)
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    # Return a simple HTML-safe representation for debugging
    items = [f"{k}: {v}" for k, v in session.items()]
    # Also fetch the user's stored role name from the database for comparison
    try:
        from models.models import User
        user = User.query.get(session['user_id'])
        db_role = user.role.role_name if user and user.role else 'N/A'
        items.append(f"db_role: {db_role}")
    except Exception as e:
        items.append(f"db_error: {e}")
    return '<pre>' + '\n'.join(items) + '</pre>'


@bp.route('/debug-nav/<role>')
def debug_nav(role):
    """Return HTML showing which nav links would be shown for the given role (debug only)."""
    if not current_app.debug:
        abort(404)
    r = (role or '').strip().lower()
    links = []
    if r == 'student':
        links = [
            ('Dashboard', url_for('student.dashboard')),
            ('Events', url_for('student.events')),
            ('My Registrations', url_for('student.my_registrations')),
            ('Certificates', url_for('student.my_certificates')),
        ]
    elif r == 'event organizer' or r == 'organizer':
        links = [
            ('Dashboard', url_for('organizer.dashboard')),
            ('Create Event', url_for('organizer.create_event')),
        ]
    elif r == 'hod':
        links = [('Dashboard', url_for('hod.dashboard'))]
    elif r == 'principal':
        links = [('Dashboard', url_for('principal.dashboard'))]
    elif r == 'admin':
        links = [
            ('Dashboard', url_for('admin.dashboard')),
            ('Events', url_for('admin.events')),
            ('Reports', url_for('admin.reports')),
            ('Feedback', url_for('admin.feedback')),
        ]
    else:
        return f"Unknown role: {role}", 400

    html = ['<h3>Navigation for role: ' + role + '</h3>', '<ul>']
    for text, href in links:
        html.append(f'<li><a href="{href}">{text}</a></li>')
    html.append('</ul>')
    return '\n'.join(html)
