"""Direct DB checks for attendance issues without importing the Flask app.
Usage:
    source venv/bin/activate
    python3 tools/check_attendance_direct.py --student-id 6
"""
import argparse
import pymysql

parser = argparse.ArgumentParser()
parser.add_argument('--student-id', type=int)
args = parser.parse_args()

# Configure DB connection (match app.py)
DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER='root'
DB_PASS='Root1234!'
DB_NAME='campus_event_db'

def get_conn():
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME, cursorclass=pymysql.cursors.DictCursor)

def student_report(sid):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, full_name, email FROM users WHERE user_id=%s', (sid,))
            user = cur.fetchone()
            if not user:
                print(f'No user with id {sid}')
                return
            print(f"User: {user['user_id']} - {user['full_name']} <{user['email']}>")

            # Registrations
            cur.execute('''SELECT r.registration_id, r.event_id, e.title, r.registered_at
                           FROM registrations r JOIN events e ON r.event_id = e.event_id
                           WHERE r.student_id=%s''', (sid,))
            regs = cur.fetchall()
            print(f"Registrations: {len(regs)}")
            for r in regs:
                print(f"  reg_id={r['registration_id']} event_id={r['event_id']} title={r['title']} registered_at={r['registered_at']}")
                # attendance
                cur.execute('SELECT * FROM attendance WHERE registration_id=%s', (r['registration_id'],))
                att = cur.fetchone()
                print(f"     attendance: {'YES' if att else 'NO'}")
                # certificate
                cur.execute('SELECT * FROM certificates WHERE student_id=%s AND event_id=%s', (sid, r['event_id']))
                cert = cur.fetchone()
                print(f"     certificate: {'YES' if cert else 'NO'}")

            # summary counts
            cur.execute('SELECT COUNT(*) AS cnt FROM registrations WHERE student_id=%s', (sid,))
            total_regs = cur.fetchone()['cnt']
            cur.execute('SELECT COUNT(*) AS cnt FROM attendance a JOIN registrations r ON a.registration_id=r.registration_id WHERE r.student_id=%s', (sid,))
            total_att = cur.fetchone()['cnt']
            print(f"\nSummary: registrations={total_regs}, attendance_rows={total_att}")
    finally:
        conn.close()

if __name__ == '__main__':
    if not args.student_id:
        print('Please provide --student-id')
    else:
        student_report(args.student_id)
