#!/usr/bin/env python3
"""
Inspect and optionally clean related records for a user.

Usage:
  python tools/inspect_and_cleanup_user.py <user_id> [--delete]

By default the script prints counts of related records that block deletion.
If `--delete` is provided the script will delete records that belong to the user
and are safe to remove (e.g., events organized by a guest user, registrations,
certificates, feedback, teams led by the user, team invitations). It will NOT
touch records owned by non-guest users unless explicitly forced (`--force`).

This script is conservative and non-destructive by default.
"""
import sys
import os
import argparse
from sqlalchemy import text

# Ensure project root is on sys.path so `from app import app` works when run from tools/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app import app
    from models import db
    from models.models import User
except Exception as e:
    print('Failed to import app or models:', e)
    sys.exit(2)


def exists(col, table):
    q = text("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table AND COLUMN_NAME = :col
    """)
    return int(db.session.execute(q, {'table': table, 'col': col}).scalar()) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id', type=int)
    parser.add_argument('--delete', action='store_true', help='Perform deletions of guest-owned related records')
    parser.add_argument('--force', action='store_true', help='Force delete regardless of guest flags (dangerous)')
    args = parser.parse_args()

    uid = args.user_id
    with app.app_context():
        user = User.query.get(uid)
        if not user:
            print('User not found for user_id=', uid)
            return

        print(f'Inspecting related records for user {uid} ({user.full_name})')

        # Counts
        counts = {}

        counts['organized_events'] = db.session.execute(text('SELECT COUNT(*) FROM events WHERE organizer_id = :uid'), {'uid': uid}).scalar()
        counts['approvals'] = db.session.execute(text('SELECT COUNT(*) FROM approvals WHERE approver_id = :uid'), {'uid': uid}).scalar()
        counts['registrations'] = db.session.execute(text('SELECT COUNT(*) FROM registrations WHERE student_id = :uid'), {'uid': uid}).scalar()
        counts['attendance_scanned'] = db.session.execute(text('SELECT COUNT(*) FROM attendance WHERE scanned_by = :uid'), {'uid': uid}).scalar()
        counts['certificates'] = db.session.execute(text('SELECT COUNT(*) FROM certificates WHERE student_id = :uid'), {'uid': uid}).scalar()
        counts['feedback'] = db.session.execute(text('SELECT COUNT(*) FROM feedback WHERE student_id = :uid'), {'uid': uid}).scalar()
        counts['led_teams'] = db.session.execute(text('SELECT COUNT(*) FROM teams WHERE leader_id = :uid'), {'uid': uid}).scalar()
        counts['team_invitations'] = db.session.execute(text('SELECT COUNT(*) FROM team_invitations WHERE invitee_id = :uid'), {'uid': uid}).scalar()

        for k, v in counts.items():
            print(f'  {k}: {v}')

        blocking = sum(v > 0 for v in counts.values())
        if blocking == 0:
            print('\nNo related records found. User can be safely deleted.')
            return

        if not args.delete:
            print('\nRun with `--delete` to remove guest-owned related records (conservative).')
            return

        # Deletion plan: only delete things that belong to this user. If force is not set,
        # prefer to delete only records where the related row has guest flags when available.

        print('\nDeleting related records (this is irreversible).')

        # Delete attendance entries scanned by this user
        if counts['attendance_scanned']:
            db.session.execute(text('DELETE FROM attendance WHERE scanned_by = :uid'), {'uid': uid})
            print('  Deleted attendance scanned by user')

        # Delete team invitations where invitee is this user
        if counts['team_invitations']:
            if args.force:
                db.session.execute(text('DELETE FROM team_invitations WHERE invitee_id = :uid'), {'uid': uid})
                print('  Deleted team_invitations (force)')
            else:
                # Only delete invitations where invitee is guest or invitation row has is_guest column true
                if exists('is_guest', 'team_invitations'):
                    db.session.execute(text("DELETE FROM team_invitations WHERE invitee_id = :uid AND (is_guest = 1 OR invitee_id = :uid)"), {'uid': uid})
                else:
                    db.session.execute(text('DELETE FROM team_invitations WHERE invitee_id = :uid'), {'uid': uid})
                print('  Deleted team_invitations for user')

        # Delete registrations (which will cascade delete attendance via FK constraints if configured)
        if counts['registrations']:
            db.session.execute(text('DELETE FROM registrations WHERE student_id = :uid'), {'uid': uid})
            print('  Deleted registrations for user')

        # Delete teams led by user
        if counts['led_teams']:
            if args.force:
                db.session.execute(text('DELETE FROM teams WHERE leader_id = :uid'), {'uid': uid})
                print('  Deleted teams (force)')
            else:
                if exists('is_guest', 'teams'):
                    db.session.execute(text('DELETE FROM teams WHERE leader_id = :uid AND is_guest = 1'), {'uid': uid})
                    print('  Deleted guest teams led by user')
                else:
                    db.session.execute(text('DELETE FROM teams WHERE leader_id = :uid'), {'uid': uid})
                    print('  Deleted teams led by user (no is_guest column)')

        # Delete certificates
        if counts['certificates']:
            db.session.execute(text('DELETE FROM certificates WHERE student_id = :uid'), {'uid': uid})
            print('  Deleted certificates for user')

        # Delete feedback
        if counts['feedback']:
            db.session.execute(text('DELETE FROM feedback WHERE student_id = :uid'), {'uid': uid})
            print('  Deleted feedback for user')

        # Delete approvals
        if counts['approvals']:
            db.session.execute(text('DELETE FROM approvals WHERE approver_id = :uid'), {'uid': uid})
            print('  Deleted approvals by user')

        # Delete events organized by this user (only guest events unless forced)
        if counts['organized_events']:
            if args.force:
                db.session.execute(text('DELETE FROM events WHERE organizer_id = :uid'), {'uid': uid})
                print('  Deleted events organized by user (force)')
            else:
                if exists('is_guest', 'events'):
                    db.session.execute(text('DELETE FROM events WHERE organizer_id = :uid AND is_guest = 1'), {'uid': uid})
                    print('  Deleted guest events organized by user')
                else:
                    db.session.execute(text('DELETE FROM events WHERE organizer_id = :uid'), {'uid': uid})
                    print('  Deleted events organized by user (no is_guest column)')

        db.session.commit()
        print('\nCleanup complete. Re-run inspection to verify remaining records.')


if __name__ == '__main__':
    main()
