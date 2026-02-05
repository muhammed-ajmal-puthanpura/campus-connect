#!/usr/bin/env python3
"""
Programmatically stamp Alembic head using the application's DB URL.
Run: python tools/alembic_stamp_head.py
"""
import sys
from alembic.config import Config
from alembic import command
import os

# ensure project root on path and load app
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from app import app

cfg = Config(os.path.join(proj_root, 'alembic.ini'))
# Use the app's SQLALCHEMY_DATABASE_URI to avoid editing alembic.ini
db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
if not db_url:
    print('Could not find DB URL in app config; set sqlalchemy.url in alembic.ini instead.')
    sys.exit(2)

# configparser treats '%' as interpolation; escape percent signs to avoid errors
escaped_db_url = db_url.replace('%', '%%')
cfg.set_main_option('sqlalchemy.url', escaped_db_url)

print('Stamping Alembic revision head using DB URL from app config...')
command.stamp(cfg, 'head')
print('Alembic stamp completed.')
