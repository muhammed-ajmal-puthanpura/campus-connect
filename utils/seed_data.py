"""
Database Seeding - Demo Data
"""

from app import db
from models.models import Role, Department, User, Venue
from datetime import datetime

def seed_database():
    """Seed database with initial data"""
    
    # Check if already seeded
    if Role.query.first():
        print("Database already seeded.")
        return
    
    print("Seeding database...")
    
    # Create Roles
    roles = [
        Role(role_name='Student'),
        Role(role_name='Event Organizer'),
        Role(role_name='HOD'),
        Role(role_name='Principal'),
        Role(role_name='Admin')
    ]
    db.session.add_all(roles)
    db.session.commit()
    
    # Create Departments
    departments = [
        Department(dept_name='Computer Science'),
        Department(dept_name='Electronics'),
        Department(dept_name='Mechanical'),
        Department(dept_name='Civil'),
        Department(dept_name='General')  # For common areas
    ]
    db.session.add_all(departments)
    db.session.commit()
    
    # Get role and department IDs
    student_role = Role.query.filter_by(role_name='Student').first()
    organizer_role = Role.query.filter_by(role_name='Event Organizer').first()
    hod_role = Role.query.filter_by(role_name='HOD').first()
    principal_role = Role.query.filter_by(role_name='Principal').first()
    admin_role = Role.query.filter_by(role_name='Admin').first()
    
    cs_dept = Department.query.filter_by(dept_name='Computer Science').first()
    ece_dept = Department.query.filter_by(dept_name='Electronics').first()
    mech_dept = Department.query.filter_by(dept_name='Mechanical').first()
    civil_dept = Department.query.filter_by(dept_name='Civil').first()
    general_dept = Department.query.filter_by(dept_name='General').first()
    
    # Create Demo Users
    users = []
    
    # Admin
    admin = User(
        full_name='Admin User',
        username='admin',
        email='admin@campus.edu',
        role_id=admin_role.role_id,
        dept_id=None
    )
    admin.set_password('admin123')
    users.append(admin)
    
    # Principal
    principal = User(
        full_name='Dr. Principal',
        username='principal',
        email='principal@campus.edu',
        role_id=principal_role.role_id,
        dept_id=None
    )
    principal.set_password('principal123')
    users.append(principal)
    
    # HODs
    hod_cs = User(
        full_name='Dr. CS Head',
        username='hod_cs',
        email='hod.cs@campus.edu',
        role_id=hod_role.role_id,
        dept_id=cs_dept.dept_id
    )
    hod_cs.set_password('hod123')
    users.append(hod_cs)
    
    hod_ece = User(
        full_name='Dr. ECE Head',
        username='hod_ece',
        email='hod.ece@campus.edu',
        role_id=hod_role.role_id,
        dept_id=ece_dept.dept_id
    )
    hod_ece.set_password('hod123')
    users.append(hod_ece)
    
    # Event Organizers
    org1 = User(
        full_name='Tech Club Organizer',
        username='organizer1',
        email='organizer1@campus.edu',
        role_id=organizer_role.role_id,
        dept_id=cs_dept.dept_id
    )
    org1.set_password('org123')
    users.append(org1)
    
    org2 = User(
        full_name='Cultural Club Organizer',
        username='organizer2',
        email='organizer2@campus.edu',
        role_id=organizer_role.role_id,
        dept_id=general_dept.dept_id
    )
    org2.set_password('org123')
    users.append(org2)
    
    # Students
    student1 = User(
        full_name='Alice Johnson',
        username='22CS001',
        email='alice@campus.edu',
        role_id=student_role.role_id,
        dept_id=cs_dept.dept_id
    )
    student1.set_password('student123')
    users.append(student1)
    
    student2 = User(
        full_name='Bob Smith',
        username='22CS002',
        email='bob@campus.edu',
        role_id=student_role.role_id,
        dept_id=cs_dept.dept_id
    )
    student2.set_password('student123')
    users.append(student2)
    
    student3 = User(
        full_name='Charlie Brown',
        username='22EC003',
        email='charlie@campus.edu',
        role_id=student_role.role_id,
        dept_id=ece_dept.dept_id
    )
    student3.set_password('student123')
    users.append(student3)
    
    db.session.add_all(users)
    db.session.commit()
    
    # Create Venues
    venues = [
        # CS Department venues
        Venue(venue_name='CS Lab 1', dept_id=cs_dept.dept_id, capacity=60),
        Venue(venue_name='CS Lab 2', dept_id=cs_dept.dept_id, capacity=60),
        Venue(venue_name='CS Seminar Hall', dept_id=cs_dept.dept_id, capacity=100),
        
        # ECE Department venues
        Venue(venue_name='ECE Lab', dept_id=ece_dept.dept_id, capacity=50),
        Venue(venue_name='ECE Seminar Hall', dept_id=ece_dept.dept_id, capacity=80),
        
        # Common venues
        Venue(venue_name='Main Auditorium', dept_id=None, capacity=500),
        Venue(venue_name='Seminar Hall A', dept_id=None, capacity=150),
        Venue(venue_name='Seminar Hall B', dept_id=None, capacity=150),
        Venue(venue_name='Open Air Theatre', dept_id=None, capacity=300),
    ]
    
    db.session.add_all(venues)
    db.session.commit()
    
    print("Database seeded successfully!")
    print("\n=== DEMO LOGIN CREDENTIALS ===")
    print("Admin: admin@campus.edu / admin123")
    print("Principal: principal@campus.edu / principal123")
    print("HOD (CS): hod.cs@campus.edu / hod123")
    print("Organizer 1: organizer1@campus.edu / org123")
    print("Organizer 2: organizer2@campus.edu / org123")
    print("Student 1: alice@campus.edu / student123")
    print("Student 2: bob@campus.edu / student123")
    print("Student 3: charlie@campus.edu / student123")
    print("===============================\n")
