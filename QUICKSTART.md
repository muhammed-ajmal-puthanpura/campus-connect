# 🚀 Quick Start Guide

## Get Started in 3 Steps!

### Step 1: Install Dependencies
```bash
pip install Flask Flask-SQLAlchemy qrcode Pillow reportlab
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open Browser
Navigate to: **http://localhost:5000**

---

## 🔐 Demo Login Credentials

### Student
**Email:** alice@campus.edu  
**Password:** student123

### Event Organizer
**Email:** organizer1@campus.edu  
**Password:** org123

### HOD (Head of Department)
**Email:** hod.cs@campus.edu  
**Password:** hod123

### Principal
**Email:** principal@campus.edu  
**Password:** principal123

### Admin
**Email:** admin@campus.edu  
**Password:** admin123

---

## ✨ Test the Complete Workflow

### 1️⃣ Create Event (as Organizer)
- Login as organizer
- Click "Create Event"
- Fill in event details
- Submit for approval

### 2️⃣ Approve Event (as HOD/Principal)
- Login as HOD or Principal
- Review pending events
- Approve the event

### 3️⃣ Register (as Student)
- Login as student
- Browse events
- Click "Register Now"
- Get your QR ticket

### 4️⃣ Mark Attendance (as Organizer)
- Login as organizer
- Go to your event
- Click "Scan QR"
- Enter student's QR code
- Attendance marked!

### 5️⃣ Download Certificate (as Student)
- Login as student
- Go to "My Certificates"
- Download your PDF certificate

---

## 📁 Project Structure

```
campus_event_system/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── README.md                 # Full documentation
├── INSTALLATION.md           # Installation guide
├── models/                   # Database models
├── routes/                   # Route handlers
├── utils/                    # Utility functions
├── templates/                # HTML templates
└── static/                   # CSS, JS, uploads
```

---

## 🎯 Key Features

✅ **Multi-role system** (5 user types)  
✅ **Approval workflow** (HOD → Principal)  
✅ **QR-based attendance**  
✅ **Automatic certificates**  
✅ **Venue clash detection**  
✅ **Feedback & ratings**  
✅ **Analytics dashboard**  
✅ **Responsive design**

---

## 📊 Database Schema

The system uses **8 core tables**:
- roles, departments, users
- venues, events, approvals
- registrations, attendance
- certificates, feedback

All tables are created automatically on first run!

---

## 🛠️ Troubleshooting

**Can't install packages?**
```bash
pip install --user Flask Flask-SQLAlchemy qrcode Pillow reportlab
```

**Port 5000 already in use?**
Edit `app.py` and change the port number.

**Database errors?**
Delete `campus_events.db` and restart.

---

## 📖 Need More Help?

- **Full Documentation:** See README.md
- **Installation Guide:** See INSTALLATION.md
- **Code Comments:** Check the source files

---

**Enjoy building your campus event management system! 🎓✨**
