"""Initialize app_config with guest defaults.
Run: python3 tools/init_guest_config.py
"""
import sys, os
# make project root importable when running from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models import db
from models.models import AppConfig


def ensure_key(key, value):
    s = AppConfig.query.get(key)
    if not s:
        s = AppConfig(key=key, value=str(value))
        db.session.add(s)
    else:
        s.value = str(value)

if __name__ == '__main__':
    with app.app_context():
        try:
            ensure_key('guest_enabled', '1')
            ensure_key('guest_validity_days', '30')
            ensure_key('guest_cleanup_policy', 'archive')
            db.session.commit()
            print('App config initialized: guest_enabled=1, guest_validity_days=30, guest_cleanup_policy=archive')
        except Exception as e:
            print('Failed to initialize app config:', e)
