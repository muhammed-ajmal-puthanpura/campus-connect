"""Replace original certificate files with the new_design files (new_ prefix).
This will:
 - Look for files `static/uploads/certificates/new_*`.
 - For each file, move it to `static/uploads/certificates/<original_name>` (without `new_`).
 - If a current original exists, it will be moved to backups folder (again) with timestamp.

Run:
    PYTHONPATH=. python3 tools/replace_with_new_certificates.py
"""
import os
import shutil
import glob
from datetime import datetime

BASE = os.path.join('static', 'uploads', 'certificates')
BACKUP_ROOT = os.path.join(BASE, 'backups')

now = datetime.now()
ts = now.strftime('%Y%m%d_%H%M%S')
backup_dir = os.path.join(BACKUP_ROOT, f'pre_replace_{ts}')

os.makedirs(backup_dir, exist_ok=True)

new_files = glob.glob(os.path.join(BASE, 'new_*'))
if not new_files:
    print('No new_ files found in', BASE)
    exit(0)

moved = 0
skipped = 0
for nf in new_files:
    fname = os.path.basename(nf)
    orig_name = fname.replace('new_', '', 1)
    dest = os.path.join(BASE, orig_name)

    # Backup existing dest if present
    if os.path.exists(dest):
        try:
            shutil.copy2(dest, backup_dir)
            print('Backed up existing original to', backup_dir)
        except Exception as e:
            print('Warning: failed to backup existing file', dest, e)

    # Move new file to destination (overwrite)
    try:
        # Use move which will overwrite if dest removed first
        if os.path.exists(dest):
            os.remove(dest)
        shutil.move(nf, dest)
        print(f'Moved {nf} -> {dest}')
        moved += 1
    except Exception as e:
        print('Failed to move', nf, e)
        skipped += 1

print(f'Done. moved={moved}, skipped={skipped}. Pre-replace backups at {backup_dir}')
