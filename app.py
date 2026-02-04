"""
Campus Event Management System - Main Application
"""

from flask import Flask, render_template, redirect, url_for, session
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# Initialize Flask app
app = Flask(__name__)

# Configuration
debug_enabled = os.getenv('FLASK_DEBUG', '0') == '1'

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:Root1234%21@127.0.0.1:3306/campus_event_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    hours=int(os.getenv('SESSION_LIFETIME_HOURS', '2'))
)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', '0') == '1' or not debug_enabled
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '280'))
}

# Initialize database
from models import db
db.init_app(app)

# Ensure DB has new columns for event mode and meeting_url (non-destructive)
def ensure_event_columns():
    from sqlalchemy import text
    # Check information_schema for columns
    check_mode = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'mode'
    """)
    check_meeting = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'meeting_url'
    """)
    check_poster = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'poster_url'
    """)
    check_scan_token = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'scan_token'
    """)
    check_cert_template = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'certificate_template_id'
    """)
    try:
        with app.app_context():
            r1 = db.session.execute(check_mode).scalar()
            r2 = db.session.execute(check_meeting).scalar()
            r3 = db.session.execute(check_poster).scalar()
            r4 = db.session.execute(check_scan_token).scalar()
            r5 = db.session.execute(check_cert_template).scalar()
            if r1 == 0:
                db.session.execute(text("ALTER TABLE events ADD COLUMN mode VARCHAR(20) DEFAULT 'offline';"))
            if r2 == 0:
                db.session.execute(text("ALTER TABLE events ADD COLUMN meeting_url VARCHAR(255) NULL;"))
            if r3 == 0:
                db.session.execute(text("ALTER TABLE events ADD COLUMN poster_url VARCHAR(255) NULL;"))
            if r4 == 0:
                db.session.execute(text("ALTER TABLE events ADD COLUMN scan_token VARCHAR(64) NULL;"))
            if r5 == 0:
                db.session.execute(text("ALTER TABLE events ADD COLUMN certificate_template_id INT NULL;"))
            # Ensure venue_id column allows NULL for online events
            check_venue_nullable = text("""
                SELECT IS_NULLABLE FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'events' AND COLUMN_NAME = 'venue_id'
            """)
            r4 = db.session.execute(check_venue_nullable).scalar()
            if r4 == 'NO':
                # Update any placeholder 0 values to NULL, then modify column to allow NULL
                try:
                    db.session.execute(text("UPDATE events SET venue_id = NULL WHERE venue_id = 0;"))
                except Exception:
                    # ignore if update fails
                    db.session.rollback()
                db.session.execute(text("ALTER TABLE events MODIFY COLUMN venue_id INT NULL;"))
            db.session.commit()
    except Exception:
        # If DB doesn't exist yet or other error, skip — db.create_all() will create columns for new installs
        db.session.rollback()


# Ensure DB has username column for users (non-destructive)
def ensure_user_columns():
    from sqlalchemy import text
    check_username = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'username'
    """)
    try:
        with app.app_context():
            r1 = db.session.execute(check_username).scalar()
            if r1 == 0:
                db.session.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(50) NULL;"))
            db.session.commit()
    except Exception:
        db.session.rollback()


# Ensure DB has certificate_templates table (non-destructive)
def ensure_certificate_template_table():
    from sqlalchemy import text
    check_table = text("""
        SELECT COUNT(*) AS cnt FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'certificate_templates'
    """)
    try:
        with app.app_context():
            exists = db.session.execute(check_table).scalar()
            if exists == 0:
                db.session.execute(text("""
                    CREATE TABLE certificate_templates (
                        template_id INT AUTO_INCREMENT PRIMARY KEY,
                        organizer_id INT NOT NULL,
                        name VARCHAR(120) NOT NULL,
                        image_url VARCHAR(255) NOT NULL,
                        is_default BOOLEAN DEFAULT 0,
                        positions TEXT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_certificate_templates_organizer
                            FOREIGN KEY (organizer_id) REFERENCES users(user_id)
                            ON DELETE CASCADE
                    )
                """))
            db.session.commit()
    except Exception:
        db.session.rollback()


# Create upload folders if they don't exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'certificates'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'certificates', 'templates'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'events'), exist_ok=True)

# Import routes (after db initialization)
from routes import auth, student, organizer, hod, principal, admin, common

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(student.bp)
app.register_blueprint(organizer.bp)
app.register_blueprint(hod.bp)
app.register_blueprint(principal.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(common.bp)

# Home route
@app.route('/')
def index():
    """Landing page - redirect based on login status"""
    if 'user_id' in session:
        role = session.get('role_name')
        if role == 'Student':
            return redirect(url_for('student.dashboard'))
        elif role == 'Event Organizer':
            return redirect(url_for('organizer.dashboard'))
        elif role == 'HOD':
            return redirect(url_for('hod.dashboard'))
        elif role == 'Principal':
            return redirect(url_for('principal.dashboard'))
        elif role == 'Admin':
            return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        # Import models
        from models import models
        
        # Create all tables
        db.create_all()

        # Ensure new event columns exist (mode, meeting_url)
        ensure_event_columns()
        ensure_user_columns()
        ensure_certificate_template_table()
        
        # Seed database with demo data (only when explicitly enabled)
        if os.getenv('SEED_DATA', '0') == '1':
            from utils.seed_data import seed_database
            seed_database()
    
    # SSL/HTTPS Configuration for camera access
    ssl_context = None
    use_https = os.getenv('USE_HTTPS', '0') == '1'
    
    if use_https:
        cert_file = os.path.join(os.path.dirname(__file__), 'certs', 'cert.pem')
        key_file = os.path.join(os.path.dirname(__file__), 'certs', 'key.pem')
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            ssl_context = (cert_file, key_file)
            print(f"\n🔒 HTTPS enabled with SSL certificates")
            print(f"   Access the app at: https://YOUR_IP:{os.getenv('PORT', '5000')}")
        else:
            # Use adhoc SSL (requires pyopenssl)
            try:
                ssl_context = 'adhoc'
                print(f"\n🔒 HTTPS enabled with adhoc SSL (self-signed)")
                print(f"   Access the app at: https://YOUR_IP:{os.getenv('PORT', '5000')}")
            except Exception as e:
                print(f"\n⚠️  Could not enable HTTPS: {e}")
                print("   Install pyopenssl: pip install pyopenssl")
                print("   Or generate certificates: python generate_ssl.py")
                ssl_context = None
    
    if not use_https:
        print(f"\n📱 Camera access requires HTTPS or localhost")
        print(f"   To enable HTTPS, set USE_HTTPS=1 in .env")
        print(f"   Or access via: http://localhost:{os.getenv('PORT', '5000')}")
    
    app.run(
        debug=debug_enabled, 
        host='0.0.0.0', 
        port=int(os.getenv('PORT', '5000')),
        ssl_context=ssl_context
    )
