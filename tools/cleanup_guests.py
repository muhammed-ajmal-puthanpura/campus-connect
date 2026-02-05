from app import app
from models import db
from models.models import User, AppConfig, Registration, Attendance, Certificate, Feedback, Role
from datetime import datetime

def run_cleanup():
    now = datetime.utcnow()
    expired = User.query.join(Role).filter(Role.role_name.ilike('guest'), User.expiry_date!=None, User.expiry_date<now).all()
    policy = 'archive'
    cfg = AppConfig.query.get('guest_cleanup_policy')
    if cfg and cfg.value:
        policy = cfg.value

    for u in expired:
        u.guest_status = 'expired'
        if policy == 'delete':
            Registration.query.filter_by(student_id=u.user_id).delete()
            Attendance.query.filter(Attendance.scanned_by==u.user_id).delete()
            Certificate.query.filter_by(student_id=u.user_id).delete()
            Feedback.query.filter_by(student_id=u.user_id).delete()
            db.session.delete(u)

    db.session.commit()
    print('Guest cleanup completed')


if __name__ == '__main__':
    with app.app_context():
        run_cleanup()
