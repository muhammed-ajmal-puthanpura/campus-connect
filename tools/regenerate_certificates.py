"""Regenerate all certificates using the current `generate_certificate` template.
Overwrites existing PDF files referenced in the `certificates` table.
Run:
    source venv/bin/activate
    python3 tools/regenerate_certificates.py
"""
from app import app
from models import db
from models.models import Certificate, User, Event
from utils.certificate_generator import generate_certificate
import os
from datetime import datetime

with app.app_context():
    certs = Certificate.query.all()
    print(f'Found {len(certs)} certificate records')
    updated = 0
    for cert in certs:
        try:
            student = User.query.get(cert.student_id)
            event = Event.query.get(cert.event_id)
            if not student or not event:
                print(f'Skipping cert id={cert.certificate_id}: missing student or event')
                continue

            filename = os.path.basename(cert.certificate_url)
            out_rel = os.path.join('static', 'uploads', 'certificates', filename)
            out_full = os.path.abspath(out_rel)

            # Ensure directory exists
            os.makedirs(os.path.dirname(out_full), exist_ok=True)

            # Prepare values
            student_name = student.full_name
            event_title = event.title
            event_date = event.date.strftime('%B %d, %Y') if event.date else ''
            organizer_name = event.organizer.full_name if event.organizer else ''

            # Generate certificate (overwrite)
            generate_certificate(student_name, event_title, event_date, organizer_name, out_full)

            # Update issued_at timestamp
            cert.issued_at = datetime.now()
            db.session.add(cert)
            db.session.commit()
            updated += 1
            print(f'Regenerated cert id={cert.certificate_id} -> {out_full}')
        except Exception as e:
            db.session.rollback()
            print('Error regenerating cert id=', getattr(cert, 'certificate_id', None), e)

    print(f'Done. Regenerated: {updated}/{len(certs)}')
