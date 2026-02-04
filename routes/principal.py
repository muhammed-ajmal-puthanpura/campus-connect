"""
Principal Routes - Final Event Approval
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models.models import Event, Approval, User
from sqlalchemy import func, or_
from models import db
from datetime import datetime
from functools import wraps
from utils.venue_utils import check_venue_clash, get_clash_message
from utils.email_utils import send_email
import os

bp = Blueprint('principal', __name__, url_prefix='/principal')

def principal_required(f):
    """Decorator to require principal login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role_name', '').lower() != 'principal':
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@principal_required
def dashboard():
    """Principal dashboard - view pending approvals"""
    principal_id = session['user_id']
    event_query = (request.args.get('event') or '').strip().lower()
    organizer_filter = request.args.get('organizer_id')
    
    # Get pending approvals for principal
    # Only show if HOD has approved (if HOD approval exists)
    pending_approvals = []
    # Query principal approvals case-insensitively
    all_principal_approvals = Approval.query.filter(
        Approval.approver_id == principal_id,
        func.lower(Approval.approver_role) == 'principal'
    ).all()
    
    for approval in all_principal_approvals:
        if approval.status == 'pending':
            # Check if there's a HOD approval
            hod_approval = Approval.query.filter(
                Approval.event_id == approval.event_id,
                func.lower(Approval.approver_role) == 'hod'
            ).first()
            
            # If no HOD approval needed OR HOD has approved, show to principal
            if not hod_approval or hod_approval.status == 'approved':
                pending_approvals.append(approval)

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
        approver_id=principal_id
    ).order_by(Approval.approved_at.desc()).all()
    all_approvals = [a for a in all_approvals if matches(a)]
    
    return render_template('principal/dashboard.html',
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
@principal_required
def approve_event(approval_id):
    """Approve or reject event"""
    principal_id = session['user_id']
    
    approval = Approval.query.filter_by(
        approval_id=approval_id,
        approver_id=principal_id,
        status='pending'
    ).first_or_404()
    
    event = approval.event
    
    # Check if HOD approval is required and completed
    hod_approval = Approval.query.filter_by(
        event_id=event.event_id,
        approver_role='HOD'
    ).first()
    
    if hod_approval and hod_approval.status != 'approved':
        flash('Waiting for HOD approval', 'warning')
        return redirect(url_for('principal.dashboard'))
    
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
                return redirect(url_for('principal.approve_event', approval_id=approval_id))
            
            # Approve
            approval.status = 'approved'
            approval.remarks = remarks
            approval.approved_at = datetime.now()
            
            # Final approval - mark event as approved
            event.status = 'approved'

            # Notify organizer on final approval
            if event.organizer and event.organizer.email:
                base_url = os.getenv('APP_BASE_URL') or request.url_root.rstrip('/')
                login_url = f"{base_url}{url_for('auth.login')}"
                subject = f"Event approved: {event.title}"
                body = (
                    f"Hello {event.organizer.full_name},\n\n"
                    "Your event has been approved by Principal.\n\n"
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
            
            # Reject the event
            event.status = 'rejected'

            # Notify organizer on first rejection
            if event.organizer and event.organizer.email:
                base_url = os.getenv('APP_BASE_URL') or request.url_root.rstrip('/')
                login_url = f"{base_url}{url_for('auth.login')}"
                subject = f"Event rejected: {event.title}"
                body = (
                    f"Hello {event.organizer.full_name},\n\n"
                    "Your event has been rejected by Principal.\n\n"
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
        
        return redirect(url_for('principal.dashboard'))
    
    return render_template('principal/approve_event.html',
                         approval=approval,
                         event=event,
                         hod_approval=hod_approval)
