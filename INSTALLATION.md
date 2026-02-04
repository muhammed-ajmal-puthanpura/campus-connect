# Installation Guide - Campus Event Management System

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for installing dependencies

## Step 1: Install Required Packages

Run the following command in your terminal:

```bash
pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Werkzeug==3.0.1 qrcode==7.4.2 Pillow==10.1.0 reportlab==4.0.7
```

Or use the requirements.txt file:

```bash
pip install -r requirements.txt
```

For systems requiring break-system-packages flag:

```bash
pip install -r requirements.txt --break-system-packages
```

## Step 2: Run the Application

### Method 1: Using the run script (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### Method 2: Direct Python execution
```bash
python app.py
```

Or:
```bash
python3 app.py
```

## Step 3: Access the Application

Once the server starts, open your web browser and navigate to:
```
http://localhost:5000
```

## Step 4: Login with Demo Credentials

Use any of these pre-configured accounts:

**Admin Account:**
- Email: admin@campus.edu
- Password: admin123

**Principal Account:**
- Email: principal@campus.edu
- Password: principal123

**HOD Account (Computer Science):**
- Email: hod.cs@campus.edu
- Password: hod123

**Event Organizer Account:**
- Email: organizer1@campus.edu
- Password: org123

**Student Account:**
- Email: alice@campus.edu
- Password: student123

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Make sure all dependencies are installed:
```bash
pip list | grep -E "Flask|qrcode|reportlab|Pillow|SQLAlchemy"
```

### Issue: "Address already in use"
**Solution:** Another application is using port 5000. Either:
1. Stop the other application
2. Change the port in app.py:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

### Issue: Database errors on first run
**Solution:** Delete the database file and restart:
```bash
rm campus_events.db
python app.py
```

### Issue: Permission denied when creating certificates
**Solution:** Ensure the uploads directory exists and has write permissions:
```bash
mkdir -p static/uploads/certificates
chmod 755 static/uploads/certificates
```

## Database Location

The SQLite database file will be created as `campus_events.db` in the project root directory on first run.

## What Happens on First Run

1. Database tables are created automatically
2. Demo data is seeded (roles, departments, users, venues)
3. Demo credentials are displayed in the console
4. Server starts on http://localhost:5000

## Testing the Complete Workflow

### As an Organizer:
1. Login as organizer1@campus.edu
2. Create a new event
3. Select venue, date, and time
4. Submit for approval

### As HOD:
1. Login as hod.cs@campus.edu
2. View pending approvals
3. Approve or reject the event

### As Principal:
1. Login as principal@campus.edu
2. Review and give final approval

### As Student:
1. Login as alice@campus.edu
2. Browse approved events
3. Register for an event
4. View your QR ticket

### As Organizer (Attendance):
1. Go to event details
2. Click "Scan QR"
3. Enter or scan the student's QR code
4. Attendance is marked automatically
5. Certificate is generated

### As Student (After Event):
1. View "My Certificates"
2. Download PDF certificate
3. Submit feedback for the event

### As Admin:
1. Login as admin@campus.edu
2. View all system statistics
3. Generate reports
4. Monitor feedback

## Production Deployment

For production deployment:

1. Change the SECRET_KEY in app.py
2. Set debug=False
3. Use a production database (MySQL/PostgreSQL):
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/campusevents'
   ```
4. Use a production WSGI server (gunicorn, uwsgi)
5. Set up proper logging
6. Configure SSL/HTTPS

## Need Help?

Refer to the README.md file for detailed documentation on:
- Project structure
- Database schema
- API endpoints
- Feature descriptions
- Customization options
