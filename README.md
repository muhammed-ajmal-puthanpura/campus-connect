# Campus Event Management System

A complete web-based event management platform for educational institutions built with Flask, SQLAlchemy, and vanilla JavaScript.

## Features

### Multi-Role System
- **Student**: Browse events, register, view QR tickets, download certificates, submit feedback
- **Event Organizer**: Create events, manage registrations, scan QR codes for attendance
- **HOD**: Approve/reject department events
- **Principal**: Final approval authority
- **Admin**: System-wide analytics, reports, and monitoring

### Core Functionality
- ✅ Complete approval workflow (Organizer → HOD → Principal)
- ✅ QR-based attendance tracking
- ✅ Automatic PDF certificate generation
- ✅ Venue clash detection
- ✅ Event registration system
- ✅ Feedback and rating system
- ✅ Comprehensive analytics and reports

## Technology Stack

**Backend:**
- Python Flask
- SQLAlchemy ORM
- SQLite (dev) / MySQL/PostgreSQL compatible

**Frontend:**
- HTML5
- CSS3 (Responsive Design)
- Vanilla JavaScript

**Libraries:**
- QRCode - QR code generation
- ReportLab - PDF certificate generation
- Werkzeug - Password hashing

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**
```bash
cd campus_event_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the application**
Open your browser and go to: `http://localhost:5000`

## Demo Credentials

The system comes pre-seeded with demo users:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@campus.edu | admin123 |
| Principal | principal@campus.edu | principal123 |
| HOD (CS) | hod.cs@campus.edu | hod123 |
| HOD (ECE) | hod.ece@campus.edu | hod123 |
| Organizer 1 | organizer1@campus.edu | org123 |
| Organizer 2 | organizer2@campus.edu | org123 |
| Student 1 | alice@campus.edu | student123 |
| Student 2 | bob@campus.edu | student123 |
| Student 3 | charlie@campus.edu | student123 |

## Project Structure

```
campus_event_system/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── models/                     # Database models
│   ├── __init__.py
│   └── models.py              # SQLAlchemy ORM models
│
├── routes/                     # Route blueprints
│   ├── __init__.py
│   ├── auth.py                # Authentication routes
│   ├── student.py             # Student routes
│   ├── organizer.py           # Organizer routes
│   ├── hod.py                 # HOD routes
│   ├── principal.py           # Principal routes
│   ├── admin.py               # Admin routes
│   └── common.py              # Common routes
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── qr_utils.py            # QR code generation/validation
│   ├── certificate_generator.py # PDF certificate creation
│   ├── venue_utils.py         # Venue clash detection
│   └── seed_data.py           # Database seeding
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── auth/                  # Authentication pages
│   ├── student/               # Student pages
│   ├── organizer/             # Organizer pages
│   ├── hod/                   # HOD pages
│   ├── principal/             # Principal pages
│   ├── admin/                 # Admin pages
│   └── common/                # Shared pages
│
└── static/                     # Static files
    ├── css/
    │   └── style.css          # Main stylesheet
    ├── js/
    │   └── main.js            # Main JavaScript
    └── uploads/
        └── certificates/       # Generated certificates
```

## Database Schema

### Tables
- **roles** - User roles
- **departments** - Academic departments
- **users** - All users (students, organizers, HODs, principal, admin)
- **venues** - Event venues
- **events** - Events created by organizers
- **approvals** - Approval workflow tracking
- **registrations** - Student event registrations
- **attendance** - QR-based attendance records
- **certificates** - Generated certificates
- **feedback** - Student feedback and ratings

## Workflow

### Event Creation & Approval
1. Organizer creates an event
2. System creates approval entries based on venue:
   - If venue belongs to a department: HOD → Principal
   - Otherwise: Principal only
3. Approvers can approve/reject with remarks
4. Venue clash detection prevents overlapping bookings
5. Event becomes visible to students once approved

### Student Registration & Attendance
1. Student browses approved events
2. Student registers for event
3. Unique QR code generated for registration
4. Student presents QR code at event
5. Organizer scans QR code
6. Attendance marked automatically
7. Certificate generated and available for download

### Certificate Generation
- Automatically generated after attendance is marked
- Contains: Student name, event name, date, organizer signature
- Available as PDF download from student dashboard

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Student
- `GET /student/dashboard` - Student dashboard
- `GET /student/events` - Browse events
- `POST /student/register/<event_id>` - Register for event
- `GET /student/my-registrations` - View registrations with QR codes
- `GET /student/my-certificates` - View certificates
- `POST /student/submit-feedback/<event_id>` - Submit feedback

### Organizer
- `GET /organizer/dashboard` - Organizer dashboard
- `POST /organizer/create-event` - Create new event
- `GET /organizer/event/<event_id>` - View event details
- `GET /organizer/scan-qr/<event_id>` - QR scanning interface
- `POST /organizer/validate-qr` - Validate QR and mark attendance

### HOD
- `GET /hod/dashboard` - HOD dashboard
- `POST /hod/approve-event/<approval_id>` - Approve/reject event

### Principal
- `GET /principal/dashboard` - Principal dashboard
- `POST /principal/approve-event/<approval_id>` - Approve/reject event

### Admin
- `GET /admin/dashboard` - Admin dashboard with statistics
- `GET /admin/events` - View all events with filters
- `GET /admin/reports` - Generate reports
- `GET /admin/feedback` - View all feedback

## Features in Detail

### Venue Clash Detection
The system automatically checks for venue conflicts when approving events:
- Same venue + Same date + Overlapping time = Rejection
- Prevents double-booking of facilities

### QR Code System
- Each registration generates a unique QR code
- QR code contains: Registration ID, Event ID, Student ID
- One-time scan prevents duplicate attendance marking
- Organizers can scan using mobile camera or manual input

### Certificate Generation
- Professional PDF certificates using ReportLab
- Landscape orientation with branded design
- Only issued after attendance confirmation
- Includes event details and organizer signature

### Approval Workflow
Smart routing based on venue ownership:
- Department venues require HOD approval first
- Common venues go directly to Principal
- Sequential approval process
- Complete audit trail with remarks

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control (RBAC)
- Protected routes with decorators
- Input validation and sanitization

## Responsive Design

- Mobile-friendly interface
- Adaptive layouts for all screen sizes
- Touch-friendly buttons and forms
- Optimized for tablets and phones

## Customization

### Adding New Departments
Edit `utils/seed_data.py` and add to the departments list

### Changing Theme Colors
Edit CSS variables in `static/css/style.css`:
```css
:root {
    --primary-color: #2563eb;
    --success-color: #10b981;
    /* etc. */
}
```

### Database Migration to Production
Replace SQLite with MySQL/PostgreSQL by changing:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/dbname'
```

## Troubleshooting

**Issue: Database not found**
- Solution: Delete `campus_events.db` and restart app.py

**Issue: QR code not generating**
- Solution: Check qrcode and Pillow are installed

**Issue: Certificate not downloading**
- Solution: Ensure `static/uploads/certificates/` folder exists

## Future Enhancements

- Email notifications
- SMS alerts
- Mobile app integration
- Advanced analytics dashboard
- Event calendar view
- Bulk certificate generation
- Excel report export

## License

This project is created for educational purposes.

## Support

For issues or questions, refer to the code comments or documentation within each module.

---

**Developed with Flask, SQLAlchemy, and ❤️**
