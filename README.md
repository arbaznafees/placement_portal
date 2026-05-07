# Placement Portal Application

A Flask-based web application for managing campus placement activities involving students, companies, and placement drives.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Access the Portal
Open your browser and go to: `http://127.0.0.1:5000`

## Default Admin Credentials
- **Email**: admin@placement.com
- **Password**: admin123

## Features
- Multi-role authentication (Admin, Company, Student)
- Company registration with admin approval
- Placement drive creation and management
- Student application system
- Real-time application status tracking
- Search and filter capabilities
- Blacklist management
- Resume upload functionality

## Tech Stack
- **Backend**: Flask 3.0.0
- **Database**: SQLite with Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5.3, Jinja2 templates
- **Security**: Werkzeug password hashing

## Database Schema
The application uses 5 main tables:
1. Admin - System administrators
2. Company - Registered companies
3. Student - Registered students
4. PlacementDrive - Job postings by companies
5. Application - Student applications to drives

## Project Structure
```
placement_portal/
├── app.py                  # Main application file
├── models.py               # Database models
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── admin/
│   ├── company/
│   └── student/
└── static/
    ├── css/
    │   └── style.css
    └── uploads/            # Resume storage
```

## User Workflows

### Admin
1. Login with default credentials
2. Approve/reject company registrations
3. Approve/reject placement drives
4. Manage students and companies
5. View all applications

### Company
1. Register and wait for admin approval
2. Login after approval
3. Create placement drives
4. View student applications
5. Update application status (Shortlist/Select/Reject)

### Student
1. Self-register
2. Login and complete profile
3. Browse approved placement drives
4. Apply to eligible drives
5. Track application status

## Important Notes
- Database is automatically created on first run
- All passwords are securely hashed
- Students can only apply once per drive
- CGPA eligibility is automatically checked
- Application deadlines are enforced

## Support
For any issues, please check:
1. Python version 3.8 or higher is installed
2. All dependencies are correctly installed
3. Port 5000 is not in use by another application
