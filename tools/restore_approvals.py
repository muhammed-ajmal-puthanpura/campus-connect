"""
Restore approval history for events after approvals table truncation.
"""

from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db
from models.models import Approval, Event, User, Venue


def _status_to_approval(event_status: str):
    status = (event_status or '').strip().lower()
    if status in {'approved', 'rejected'}:
        return status
    return 'pending'


def _get_approval_timestamp(event):
    return event.created_at or datetime.utcnow()


def restore_approvals():
    with app.app_context():
        events = Event.query.all()
        principal = User.query.join(User.role).filter(
            User.role.has(role_name='Principal')
        ).first()

        restored_count = 0
        skipped_count = 0

        for event in events:
            existing = Approval.query.filter_by(event_id=event.event_id).count()
            if existing > 0:
                skipped_count += 1
                continue

            approvals_to_add = []
            approval_status = _status_to_approval(event.status)
            approved_at = _get_approval_timestamp(event) if approval_status != 'pending' else None

            # Determine department for HOD check
            venue = Venue.query.get(event.venue_id) if event.venue_id else None
            dept_to_check = venue.dept_id if venue and venue.dept_id else event.dept_id

            if dept_to_check:
                hod = User.query.join(User.role).filter(
                    User.dept_id == dept_to_check,
                    User.role.has(role_name='HOD')
                ).first()
                if hod:
                    approvals_to_add.append(
                        Approval(
                            event_id=event.event_id,
                            approver_id=hod.user_id,
                            approver_role='HOD',
                            status=approval_status,
                            remarks='Auto-restored approval record',
                            approved_at=approved_at
                        )
                    )

            if principal:
                approvals_to_add.append(
                    Approval(
                        event_id=event.event_id,
                        approver_id=principal.user_id,
                        approver_role='Principal',
                        status=approval_status,
                        remarks='Auto-restored approval record',
                        approved_at=approved_at
                    )
                )

            if approvals_to_add:
                db.session.add_all(approvals_to_add)
                restored_count += 1

        db.session.commit()

        print(f"Restored approvals for {restored_count} events. Skipped {skipped_count} events with existing approvals.")


if __name__ == '__main__':
    restore_approvals()
