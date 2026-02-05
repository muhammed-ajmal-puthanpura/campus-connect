#!/usr/bin/env python3
"""
Create a `Guest` role and map existing guest users to it.

This script is non-destructive: it will create the role if missing and update
`users.role_id` for rows where `users.is_guest` is true. It will also update
`events`, `teams`, `team_invitations`, and `certificate_templates` `is_guest`
flags to be consistent with users marked as guests.

Run: `PYTHONPATH=. python tools/migrate_users_to_guest_role.py`
"""
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db
from models.models import Role, User, Event, Team, TeamInvitation, CertificateTemplate
from sqlalchemy import text

def find_or_create_guest_role():
    guest_role = Role.query.filter(Role.role_name.ilike('guest')).first()
    if guest_role:
        return guest_role
    guest_role = Role(role_name='Guest')
    db.session.add(guest_role)
    db.session.commit()
    return guest_role

def main():
    with app.app_context():
        guest_role = find_or_create_guest_role()
        print('Guest role id:', guest_role.role_id)

        # Update users that are marked as guests to use the Guest role
        users_to_update = User.query.filter(User.is_guest == True).all()
        updated_users = 0
        for u in users_to_update:
            if u.role_id != guest_role.role_id:
                u.role_id = guest_role.role_id
                updated_users += 1
        db.session.commit()
        print(f'Updated {updated_users} user(s) to Guest role')

        # Make related tables' is_guest flags consistent (if columns exist)
        conn = db.session.connection()

        def col_exists(table, col):
            q = text("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table AND COLUMN_NAME = :col
            """)
            return int(conn.execute(q, {'table': table, 'col': col}).scalar()) > 0

        # events.is_guest
        if col_exists('events', 'is_guest'):
            updated = conn.execute(text("""
                UPDATE events SET is_guest = 1
                WHERE organizer_id IN (SELECT user_id FROM users WHERE role_id = :rid)
            """), {'rid': guest_role.role_id}).rowcount
            print(f'events.is_guest set for {updated} row(s)')

        # teams.is_guest
        if col_exists('teams', 'is_guest'):
            updated = conn.execute(text("""
                UPDATE teams SET is_guest = 1
                WHERE leader_id IN (SELECT user_id FROM users WHERE role_id = :rid)
            """), {'rid': guest_role.role_id}).rowcount
            print(f'teams.is_guest set for {updated} row(s)')

        # team_invitations.is_guest
        if col_exists('team_invitations', 'is_guest'):
            updated = conn.execute(text("""
                UPDATE team_invitations SET is_guest = 1
                WHERE invitee_id IN (SELECT user_id FROM users WHERE role_id = :rid)
            """), {'rid': guest_role.role_id}).rowcount
            print(f'team_invitations.is_guest set for {updated} row(s)')

        # certificate_templates.is_guest
        if col_exists('certificate_templates', 'is_guest'):
            updated = conn.execute(text("""
                UPDATE certificate_templates SET is_guest = 1
                WHERE organizer_id IN (SELECT user_id FROM users WHERE role_id = :rid)
            """), {'rid': guest_role.role_id}).rowcount
            print(f'certificate_templates.is_guest set for {updated} row(s)')

        db.session.commit()
        print('Migration complete.')

if __name__ == '__main__':
    main()
