"""
HOD Routes - Approve/Reject Events for Department
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models.models import Event, Approval, User, Venue
from models import db
from sqlalchemy import or_
from datetime import datetime
from functools import wraps
from utils.venue_utils import check_venue_clash, get_clash_message
from utils.email_utils import send_email
import os

bp = Blueprint('hod', __name__, url_prefix='/hod')

def hod_required(f):
    """Decorator to require HOD login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role_name', '').lower() != 'hod':
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@hod_required
def dashboard():
    """HOD dashboard - view pending approvals"""
    hod_id = session['user_id']
    event_query = (request.args.get('event') or '').strip().lower()
    organizer_filter = request.args.get('organizer_id')
    
    # Get pending approvals for this HOD
    pending_approvals = Approval.query.filter_by(
        approver_id=hod_id,
        status='pending'
    ).all()
    
    def matches(approval):
        if event_query and event_query not in (approval.event.title or '').lower():
            return False
        if organizer_filter:
            try:
                if approval.event.organizer_id != int(organizer_filter):
                    return False
            except ValueError:
                return False
        return True

    pending_approvals = [a for a in pending_approvals if matches(a)]

    # Get all approvals (history)
    all_approvals = Approval.query.filter_by(
        approver_id=hod_id
    ).order_by(Approval.approved_at.desc()).all()
    all_approvals = [a for a in all_approvals if matches(a)]
    
    return render_template('hod/dashboard.html',
                         pending_approvals=pending_approvals,
                         all_approvals=all_approvals,
                         event_query=event_query,
                         organizer_filter=organizer_filter,
                         organizers=User.query.join(User.role).filter(
                             or_(
                                 User.role.has(role_name='Event Organizer'),
                                 User.role.has(role_name='Organizer')
                             )
                         ).order_by(User.full_name.asc()).all())


@bp.route('/approve-event/<int:approval_id>', methods=['GET', 'POST'])
@hod_required
def approve_event(approval_id):
    """Approve or reject event"""
    hod_id = session['user_id']
    
    approval = Approval.query.filter_by(
        approval_id=approval_id,
        approver_id=hod_id,
        status='pending'
    ).first_or_404()
    
    event = approval.event
    
    if request.method == 'POST':
        action = request.form.get('action')
        remarks = request.form.get('remarks')
        
        if action == 'approve':
            # Check for venue clash before approving
            clash_info = check_venue_clash(
                event.venue_id,
                event.date,
                event.start_time,
                event.end_time,
                event.event_id
            )
            
            if clash_info['clash']:
                flash(get_clash_message(clash_info['conflicting_events']), 'error')
                return redirect(url_for('hod.approve_event', approval_id=approval_id))
            
            # Approve this stage
            approval.status = 'approved'
            approval.remarks = remarks
            approval.approved_at = datetime.now()
            
            # Check if all required approvals are complete
            all_approvals = Approval.query.filter_by(event_id=event.event_id).all()
            
            # If this is the only approval needed (no Principal approval after)
            # or if Principal has also approved, mark event as approved
            # Find principal approval in a case-insensitive way
            principal_approval = next(
                (a for a in all_approvals if (a.approver_role or '').strip().lower() == 'principal'),
                None
            )

            if principal_approval and principal_approval.status == 'pending':
                principal = principal_approval.approver
                if principal and principal.email:
                    base_url = os.getenv('APP_BASE_URL') or request.url_root.rstrip('/')
                    login_url = f"{base_url}{url_for('auth.login')}"
                    subject = f"Event awaiting your approval: {event.title}"
                    body = (
                        f"Hello {principal.full_name},\n\n"
                        "An event has been approved by HOD and is awaiting your approval.\n\n"
                        f"Event: {event.title}\n"
                        f"Organizer: {event.organizer.full_name if event.organizer else 'N/A'}\n"
                        f"Date: {event.date.strftime('%Y-%m-%d')}\n"
                        f"Time: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n\n"
                        f"Login: {login_url}\n"
                    )
                    try:
                        send_email(principal.email, subject, body)
                    except Exception as exc:
                        current_app.logger.warning(f"Principal email send failed: {exc}")

            if not principal_approval or principal_approval.status == 'approved':
                event.status = 'approved'
                # Notify organizer on final approval
                if event.organizer and event.organizer.email:
                    base_url = os.getenv('APP_BASE_URL') or request.url_root.rstrip('/')
                    login_url = f"{base_url}{url_for('auth.login')}"
                    subject = f"Event approved: {event.title}"
                    body = (
                        f"Hello {event.organizer.full_name},\n\n"
                        "Your event has been approved.\n\n"
                        f"Event: {event.title}\n"
                        f"Date: {event.date.strftime('%Y-%m-%d')}\n"
                        f"Time: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n\n"
                        f"Login: {login_url}\n"
                    )
                    try:
                        send_email(event.organizer.email, subject, body)
                    except Exception as exc:
                        current_app.logger.warning(f"Organizer approval email failed: {exc}")
            
            db.session.commit()
            flash('Event approved successfully!', 'success')
            
        elif action == 'reject':
            approval.status = 'rejected'
            approval.remarks = remarks
            approval.approved_at = datetime.now()
            
            # Reject the entire event
            event.status = 'rejected'
            
            # Reject all other pending approvals for this event
            other_approvals = Approval.query.filter_by(
                event_id=event.event_id,
                status='pending'
            ).all()
            
            for other in other_approvals:
                other.status = 'rejected'
                other.remarks = 'Rejected at HOD level'
                other.approved_at = datetime.now()

            # Notify organizer on first rejection
            if event.organizer and event.organizer.email:
                base_url = os.getenv('APP_BASE_URL') or request.url_root.rstrip('/')
                login_url = f"{base_url}{url_for('auth.login')}"
                subject = f"Event rejected: {event.title}"
                body = (
                    f"Hello {event.organizer.full_name},\n\n"
                    "Your event has been rejected at HOD level.\n\n"
                    f"Event: {event.title}\n"
                    f"Remarks: {remarks or 'N/A'}\n\n"
                    f"Login: {login_url}\n"
                )
                try:
                    send_email(event.organizer.email, subject, body)
                except Exception as exc:
                    current_app.logger.warning(f"Organizer rejection email failed: {exc}")
            
            db.session.commit()
            flash('Event rejected', 'info')
        
        return redirect(url_for('hod.dashboard'))
    
    return render_template('hod/approve_event.html',
                         approval=approval,
                         event=event)
