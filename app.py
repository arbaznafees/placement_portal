
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Admin, Company, Student, PlacementDrive, Application
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """
    Load user based on user_id format: {role}_{id}
    This function is called by Flask-Login to reload user object from session
    """
    if user_id.startswith('admin_'):
        return Admin.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('company_'):
        return Company.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('student_'):
        return Student.query.get(int(user_id.split('_')[1]))
    return None

def get_user_role(user):
    """Helper function to determine user role"""
    if isinstance(user, Admin):
        return 'admin'
    elif isinstance(user, Company):
        return 'company'
    elif isinstance(user, Student):
        return 'student'
    return None

# ==================== HOME & AUTH ROUTES ====================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route for all user types"""
    if current_user.is_authenticated:
        role = get_user_role(current_user)
        return redirect(url_for(f'{role}_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        user = None
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
        elif role == 'company':
            user = Company.query.filter_by(email=email).first()
            if user and user.is_blacklisted:
                flash('Your account has been blacklisted. Contact admin.', 'danger')
                return redirect(url_for('login'))
            if user and not user.is_approved:
                flash('Your account is pending approval. Please wait for admin approval.', 'warning')
                return redirect(url_for('login'))
        elif role == 'student':
            user = Student.query.filter_by(email=email).first()
            if user and user.is_blacklisted:
                flash('Your account has been blacklisted. Contact admin.', 'danger')
                return redirect(url_for('login'))
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {getattr(user, "name", getattr(user, "username", user.email))}!', 'success')
            return redirect(url_for(f'{role}_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration route for Company and Student"""
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        role = request.form.get('role')
        
        if role == 'company':
            # Company Registration
            company = Company(
                company_name=request.form.get('company_name'),
                email=request.form.get('email'),
                hr_name=request.form.get('hr_name'),
                hr_contact=request.form.get('hr_contact'),
                website=request.form.get('website'),
                description=request.form.get('description')
            )
            company.set_password(request.form.get('password'))
            
            try:
                db.session.add(company)
                db.session.commit()
                flash('Company registered successfully! Wait for admin approval to login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Email already exists or invalid data!', 'danger')
        
        elif role == 'student':
            # Student Registration
            student = Student(
                roll_number=request.form.get('roll_number'),
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                department=request.form.get('department'),
                cgpa=float(request.form.get('cgpa')),
                graduation_year=int(request.form.get('graduation_year')),
                skills=request.form.get('skills')
            )
            student.set_password(request.form.get('password'))
            
            try:
                db.session.add(student)
                db.session.commit()
                flash('Registration successful! You can now login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Roll number or email already exists!', 'danger')
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    # Get statistics
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    
    pending_companies = Company.query.filter_by(is_approved=False, is_blacklisted=False).count()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').count()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_companies=total_companies,
                         total_drives=total_drives,
                         total_applications=total_applications,
                         pending_companies=pending_companies,
                         pending_drives=pending_drives)

@app.route('/admin/companies')
@login_required
def admin_companies():
    """View and manage all companies"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '')
    if search_query:
        companies = Company.query.filter(
            (Company.company_name.contains(search_query)) | 
            (Company.email.contains(search_query))
        ).all()
    else:
        companies = Company.query.all()
    
    return render_template('admin/companies.html', companies=companies, search_query=search_query)

@app.route('/admin/approve_company/<int:company_id>')
@login_required
def admin_approve_company(company_id):
    """Approve a company"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    company = Company.query.get_or_404(company_id)
    company.is_approved = True
    db.session.commit()
    flash(f'{company.company_name} has been approved!', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/reject_company/<int:company_id>')
@login_required
def admin_reject_company(company_id):
    """Reject a company"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    company = Company.query.get_or_404(company_id)
    company.is_approved = False
    db.session.commit()
    flash(f'{company.company_name} has been rejected!', 'warning')
    return redirect(url_for('admin_companies'))

@app.route('/admin/blacklist_company/<int:company_id>')
@login_required
def admin_blacklist_company(company_id):
    """Blacklist a company"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if company.is_blacklisted else 'unblacklisted'
    flash(f'{company.company_name} has been {status}!', 'info')
    return redirect(url_for('admin_companies'))

@app.route('/admin/delete_company/<int:company_id>')
@login_required
def admin_delete_company(company_id):
    """Delete a company"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash(f'{company.company_name} has been deleted!', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/students')
@login_required
def admin_students():
    """View and manage all students"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '')
    if search_query:
        students = Student.query.filter(
            (Student.name.contains(search_query)) | 
            (Student.roll_number.contains(search_query)) |
            (Student.email.contains(search_query))
        ).all()
    else:
        students = Student.query.all()
    
    return render_template('admin/students.html', students=students, search_query=search_query)

@app.route('/admin/blacklist_student/<int:student_id>')
@login_required
def admin_blacklist_student(student_id):
    """Blacklist a student"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    status = 'blacklisted' if student.is_blacklisted else 'unblacklisted'
    flash(f'{student.name} has been {status}!', 'info')
    return redirect(url_for('admin_students'))

@app.route('/admin/delete_student/<int:student_id>')
@login_required
def admin_delete_student(student_id):
    """Delete a student"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f'{student.name} has been deleted!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/drives')
@login_required
def admin_drives():
    """View and manage all placement drives"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives)

@app.route('/admin/approve_drive/<int:drive_id>')
@login_required
def admin_approve_drive(drive_id):
    """Approve a placement drive"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" has been approved!', 'success')
    return redirect(url_for('admin_drives'))

@app.route('/admin/reject_drive/<int:drive_id>')
@login_required
def admin_reject_drive(drive_id):
    """Reject a placement drive"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Rejected'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" has been rejected!', 'warning')
    return redirect(url_for('admin_drives'))

@app.route('/admin/applications')
@login_required
def admin_applications():
    """View all applications"""
    if not isinstance(current_user, Admin):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    applications = Application.query.order_by(Application.application_date.desc()).all()
    return render_template('admin/applications.html', applications=applications)

# ==================== COMPANY ROUTES ====================

@app.route('/company/dashboard')
@login_required
def company_dashboard():
    """Company dashboard"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    # Get company's drives and statistics
    drives = PlacementDrive.query.filter_by(company_id=current_user.id).order_by(PlacementDrive.created_at.desc()).all()
    total_applications = sum([len(drive.applications) for drive in drives])
    
    return render_template('company/dashboard.html', 
                         drives=drives, 
                         total_applications=total_applications)

@app.route('/company/create_drive', methods=['GET', 'POST'])
@login_required
def company_create_drive():
    """Create a new placement drive"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        drive = PlacementDrive(
            company_id=current_user.id,
            job_title=request.form.get('job_title'),
            job_description=request.form.get('job_description'),
            eligibility_criteria=request.form.get('eligibility_criteria'),
            min_cgpa=float(request.form.get('min_cgpa', 0)),
            salary_package=request.form.get('salary_package'),
            job_location=request.form.get('job_location'),
            application_deadline=datetime.strptime(request.form.get('application_deadline'), '%Y-%m-%d')
        )
        
        db.session.add(drive)
        db.session.commit()
        flash('Placement drive created successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company/create_drive.html')

@app.route('/company/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
@login_required
def company_edit_drive(drive_id):
    """Edit a placement drive"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.eligibility_criteria = request.form.get('eligibility_criteria')
        drive.min_cgpa = float(request.form.get('min_cgpa', 0))
        drive.salary_package = request.form.get('salary_package')
        drive.job_location = request.form.get('job_location')
        drive.application_deadline = datetime.strptime(request.form.get('application_deadline'), '%Y-%m-%d')
        
        db.session.commit()
        flash('Drive updated successfully!', 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company/edit_drive.html', drive=drive)

@app.route('/company/delete_drive/<int:drive_id>')
@login_required
def company_delete_drive(drive_id):
    """Delete a placement drive"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('company_dashboard'))
    
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted successfully!', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/company/close_drive/<int:drive_id>')
@login_required
def company_close_drive(drive_id):
    """Close a placement drive"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('company_dashboard'))
    
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed successfully!', 'info')
    return redirect(url_for('company_dashboard'))

@app.route('/company/applications/<int:drive_id>')
@login_required
def company_applications(drive_id):
    """View applications for a specific drive"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('company_dashboard'))
    
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('company/applications.html', drive=drive, applications=applications)

@app.route('/company/update_application/<int:application_id>/<status>')
@login_required
def company_update_application(application_id, status):
    """Update application status (Shortlisted/Selected/Rejected)"""
    if not isinstance(current_user, Company):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    
    if application.placement_drive.company_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('company_dashboard'))
    
    if status in ['Shortlisted', 'Selected', 'Rejected']:
        application.status = status
        db.session.commit()
        flash(f'Application status updated to {status}!', 'success')
    
    return redirect(url_for('company_applications', drive_id=application.drive_id))

# ==================== STUDENT ROUTES ====================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student dashboard"""
    if not isinstance(current_user, Student):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    # Get approved drives
    approved_drives = PlacementDrive.query.filter_by(status='Approved').order_by(PlacementDrive.application_deadline).all()
    
    # Get student's applications
    my_applications = Application.query.filter_by(student_id=current_user.id).all()
    applied_drive_ids = [app.drive_id for app in my_applications]
    
    return render_template('student/dashboard.html', 
                         approved_drives=approved_drives,
                         my_applications=my_applications,
                         applied_drive_ids=applied_drive_ids)

@app.route('/student/drives')
@login_required
def student_drives():
    """View all approved placement drives"""
    if not isinstance(current_user, Student):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    approved_drives = PlacementDrive.query.filter_by(status='Approved').order_by(PlacementDrive.application_deadline).all()
    my_applications = Application.query.filter_by(student_id=current_user.id).all()
    applied_drive_ids = [app.drive_id for app in my_applications]
    
    return render_template('student/drives.html', drives=approved_drives, applied_drive_ids=applied_drive_ids)

@app.route('/student/apply/<int:drive_id>', methods=['POST'])
@login_required
def student_apply(drive_id):
    """Apply for a placement drive"""
    if not isinstance(current_user, Student):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if already applied
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied for this drive!', 'warning')
        return redirect(url_for('student_drives'))
    
    # Check eligibility
    if current_user.cgpa < drive.min_cgpa:
        flash(f'You do not meet the minimum CGPA requirement ({drive.min_cgpa})', 'danger')
        return redirect(url_for('student_drives'))
    
    # Check deadline
    if drive.application_deadline < datetime.utcnow():
        flash('Application deadline has passed!', 'danger')
        return redirect(url_for('student_drives'))
    
    # Create application
    application = Application(
        student_id=current_user.id,
        drive_id=drive_id,
        cover_letter=request.form.get('cover_letter')
    )
    
    db.session.add(application)
    db.session.commit()
    flash(f'Successfully applied for {drive.job_title}!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    """View and edit student profile"""
    if not isinstance(current_user, Student):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        current_user.department = request.form.get('department')
        current_user.cgpa = float(request.form.get('cgpa'))
        current_user.graduation_year = int(request.form.get('graduation_year'))
        current_user.skills = request.form.get('skills')
        
        # Handle resume upload
        if 'resume' in request.files:
            resume = request.files['resume']
            if resume.filename:
                # Create uploads folder if not exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = f"{current_user.roll_number}_{resume.filename}"
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resume.save(resume_path)
                current_user.resume_path = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
    
    return render_template('student/profile.html')

@app.route('/student/application_history')
@login_required
def student_application_history():
    """View application history"""
    if not isinstance(current_user, Student):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.application_date.desc()).all()
    return render_template('student/application_history.html', applications=applications)

# ==================== INITIALIZE DATABASE ====================

def init_db():
    """Initialize database and create admin user"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin', email='admin@placement.com')
            admin.set_password('admin123')  # Change this password!
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin created (username: admin, password: admin123)")
        else:
            print("✓ Admin already exists")

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    print("\n=== Placement Portal Starting ===")
    print("Admin Login: admin@placement.com / admin123")
    print("Access the app at: http://127.0.0.1:5000")
    print("===================================\n")
    
    app.run(debug=True)
