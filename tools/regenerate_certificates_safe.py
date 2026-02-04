"""Safely regenerate certificates with backups and new filenames.
Backups are placed under `static/uploads/certificates/backups/<timestamp>/`.
New files are written as `static/uploads/certificates/new_<orig>` and DB records are updated to point to `uploads/certificates/new_<orig>`.

Run:
    source venv/bin/activate
    python3 tools/regenerate_certificates_safe.py
"""
from app import app
from models import db
from models.models import Certificate, User, Event
from utils.certificate_generator import generate_certificate
import os
import shutil
from datetime import datetime

BACKUP_ROOT = os.path.join('static', 'uploads', 'certificates', 'backups')
OUT_DIR = os.path.join('static', 'uploads', 'certificates')

with app.app_context():
    now = datetime.now()
    ts = now.strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    certs = Certificate.query.all()
    print(f'Found {len(certs)} certificate records')
    regenerated = 0
    for cert in certs:
        try:
            student = User.query.get(cert.student_id)
            event = Event.query.get(cert.event_id)
            if not student or not event:
                print(f'Skipping cert id={cert.certificate_id}: missing student or event')
                continue

            # Resolve original file path
            orig_rel = cert.certificate_url or ''
            if orig_rel.startswith('uploads/'):
                orig_full = os.path.join('static', orig_rel)
            elif orig_rel.startswith('static/'):
                orig_full = orig_rel
            else:
                orig_full = os.path.join('static', 'uploads', 'certificates', os.path.basename(orig_rel))

            # Backup original if exists
            if os.path.exists(orig_full):
                try:
                    shutil.copy2(orig_full, backup_dir)
                except Exception as e:
                    print('Warning: failed to backup', orig_full, e)

            # New filename
            orig_name = os.path.basename(orig_full)
            new_name = f'new_{orig_name}'
            out_full = os.path.join(OUT_DIR, new_name)

            # Generate friendly fields
            student_name = student.full_name
            event_title = event.title
            event_date = event.date.strftime('%B %d, %Y') if event.date else ''
            organizer_name = event.organizer.full_name if event.organizer else ''

            # Generate certificate
            generate_certificate(student_name, event_title, event_date, organizer_name, out_full)

            # Update DB record to point to new file (relative path under static)
            cert.certificate_url = os.path.join('uploads', 'certificates', new_name)
            cert.issued_at = datetime.now()
            db.session.add(cert)
            db.session.commit()

            regenerated += 1
            print(f'Regenerated cert id={cert.certificate_id} -> {cert.certificate_url}')
        except Exception as e:
            db.session.rollback()
            print('Error regenerating cert id=', getattr(cert, 'certificate_id', None), e)

    print(f'Done. Regenerated: {regenerated}/{len(certs)}')
    print('Backups stored in', backup_dir)
