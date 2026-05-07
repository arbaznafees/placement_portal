"""
Database Models for Placement Portal
This file defines all database tables using SQLAlchemy ORM
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize SQLAlchemy (will be bound to app in app.py)
db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    """
    Admin model - Pre-existing superuser who manages the entire system
    """
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and store password securely"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Required by Flask-Login"""
        return f"admin_{self.id}"


class Company(UserMixin, db.Model):
    """
    Company model - Organizations that create placement drives
    """
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    hr_name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(15), nullable=False)
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval required
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One company can have many placement drives
    placement_drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"company_{self.id}"


class Student(UserMixin, db.Model):
    """
    Student model - Users who apply for placement drives
    """
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    resume_path = db.Column(db.String(200))  # Path to uploaded resume
    skills = db.Column(db.Text)  # Comma-separated skills
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One student can have many applications
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"student_{self.id}"


class PlacementDrive(db.Model):
    """
    Placement Drive model - Job postings created by companies
    """
    __tablename__ = 'placement_drive'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)  # e.g., "CGPA >= 7.0"
    min_cgpa = db.Column(db.Float, default=0.0)
    salary_package = db.Column(db.String(50))  # e.g., "10-12 LPA"
    job_location = db.Column(db.String(100))
    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Closed, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One drive can have many applications
    applications = db.relationship('Application', backref='placement_drive', lazy=True, cascade='all, delete-orphan')
    
    def is_open(self):
        """Check if drive is still accepting applications"""
        return self.status == 'Approved' and self.application_deadline > datetime.utcnow()


class Application(db.Model):
    """
    Application model - Records of students applying to placement drives
    """
    __tablename__ = 'application'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')  # Applied, Shortlisted, Selected, Rejected
    cover_letter = db.Column(db.Text)
    
    # Composite unique constraint - prevent duplicate applications
    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )
