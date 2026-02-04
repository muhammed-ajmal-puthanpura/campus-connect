"""Restore certificate DB links to original filenames using backups.
This will NOT delete new_* files; it will update `certificates.certificate_url` to point to the original filenames
(if a backup exists) so the site continues to serve original PDFs.

Run:
    PYTHONPATH=. python3 tools/restore_original_certificate_links.py
"""
from datetime import datetime
import os
import glob
from app import app
from models import db
from models.models import Certificate

# Find latest backup directory under static/uploads/certificates/backups
BACKUP_BASE = os.path.join('static', 'uploads', 'certificates', 'backups')
if not os.path.isdir(BACKUP_BASE):
    print('No backups directory found at', BACKUP_BASE)
    exit(1)

subdirs = sorted([d for d in glob.glob(os.path.join(BACKUP_BASE, '*')) if os.path.isdir(d)])
if not subdirs:
    print('No backup subdirectories found under', BACKUP_BASE)
    exit(1)

latest_backup = subdirs[-1]
print('Using backup folder:', latest_backup)

# Start restoring inside app context
restored = 0
skipped = 0
with app.app_context():
    certs = Certificate.query.all()
    for cert in certs:
        curr = cert.certificate_url or ''
        # Only attempt to restore if current points to the new_ file
        if '/new_' in curr or curr.startswith('uploads/certificates/new_'):
            base = os.path.basename(curr)
            if base.startswith('new_'):
                orig_name = base.replace('new_', '', 1)
            else:
                # fallback: remove leading 'new_'
                orig_name = base.replace('new_', '')

            backup_path = os.path.join(latest_backup, orig_name)
            original_rel = os.path.join('uploads', 'certificates', orig_name)
            original_full = os.path.join('static', 'uploads', 'certificates', orig_name)

            if os.path.exists(backup_path) or os.path.exists(original_full):
                try:
                    cert.certificate_url = original_rel
                    cert.issued_at = datetime.now()
                    db.session.add(cert)
                    db.session.commit()
                    restored += 1
                    print(f'Restored cert id={cert.certificate_id} -> {original_rel}')
                except Exception as e:
                    db.session.rollback()
                    skipped += 1
                    print('Error restoring cert id=', cert.certificate_id, e)
            else:
                skipped += 1
                print(f'Skipped cert id={cert.certificate_id}: original file not found in backup or output folder')
        else:
            # already original or not managed
            skipped += 1

print(f'Done. Restored: {restored}, Skipped: {skipped}')
