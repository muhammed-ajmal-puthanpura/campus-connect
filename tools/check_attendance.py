"""Run quick checks for attendance/certificate mismatches.
Usage:
    source venv/bin/activate
    python3 tools/check_attendance.py [--student-id ID] [--email user@example.com]

If no args provided, script prints summary counts and lists problematic registrations.
"""
import sys
import argparse
from app import app, db
from models.models import Registration, Attendance, Certificate, Event, User

parser = argparse.ArgumentParser()
parser.add_argument('--student-id', type=int)
parser.add_argument('--email', type=str)
args = parser.parse_args()

with app.app_context():
    def get_student_id():
        if args.student_id:
            return args.student_id
        if args.email:
            user = User.query.filter_by(email=args.email).first()
            return user.user_id if user else None
        return None

    sid = get_student_id()

    # Overall counts
    total_regs = Registration.query.count()
    total_att = Attendance.query.count()
    total_certs = Certificate.query.count()

    print(f"Total registrations: {total_regs}")
    print(f"Total attendance rows: {total_att}")
    print(f"Total certificates: {total_certs}\n")

    # If a student specified, show their stats
    if sid:
        regs = Registration.query.filter_by(student_id=sid).all()
        print(f"Student {sid} registrations: {len(regs)}")
        for r in regs:
            att = Attendance.query.filter_by(registration_id=r.registration_id).first()
            cert = Certificate.query.filter_by(student_id=r.student_id, event_id=r.event_id).first()
            print(f"  reg_id={r.registration_id} event={r.event.title} event_id={r.event_id} registered_at={r.registered_at}")
            print(f"     attendance: {'YES' if att else 'NO'} (attendance_id={att.attendance_id if att else 'N/A'})")
            print(f"     certificate: {'YES' if cert else 'NO'} (cert_id={cert.certificate_id if cert else 'N/A'})")
        sys.exit(0)

    # Find registrations that have certificates but no attendance
    rows = db.session.query(Registration).join(Certificate, (Certificate.student_id==Registration.student_id) & (Certificate.event_id==Registration.event_id)).outerjoin(Attendance).filter(Attendance.attendance_id==None).all()
    if rows:
        print('Registrations with certificate but no attendance:')
        for r in rows:
            print(f"  reg_id={r.registration_id} student_id={r.student_id} event_id={r.event_id} event_title={r.event.title}")
    else:
        print('No registrations with certificate but missing attendance found.')

    # Find attendance rows not linked to registration (shouldn't happen)
    orphan_att = db.session.query(Attendance).outerjoin(Registration).filter(Registration.registration_id==None).all()
    if orphan_att:
        print('\nAttendance rows without registration record:')
        for a in orphan_att:
            print(f'  attendance_id={a.attendance_id} registration_id={a.registration_id}')

    print('\nDone.')
