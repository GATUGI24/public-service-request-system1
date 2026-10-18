import os
from flask import (Flask, render_template, redirect, url_for, request,
                   flash, send_from_directory)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, ServiceRequest
from datetime import datetime

# ---------- App Config ----------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')


# ----- Citizen Registration -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='citizen'
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# ----- Login -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome, {user.name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('citizen_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


# ----- Citizen Dashboard -----
@app.route('/dashboard')
@login_required
def citizen_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    requests = ServiceRequest.query.filter_by(user_id=current_user.id)\
                                   .order_by(ServiceRequest.created_at.desc()).all()
    counts = {
        'Pending':     sum(1 for r in requests if r.status == 'Pending'),
        'In Progress': sum(1 for r in requests if r.status == 'In Progress'),
        'Resolved':    sum(1 for r in requests if r.status == 'Resolved'),
    }
    return render_template('citizen_dashboard.html', requests=requests, counts=counts)


# ----- Submit Request -----
@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_request():
    if current_user.role != 'citizen':
        flash('Only citizens can submit requests.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        category = request.form['category']
        location = request.form['location'].strip()
        description = request.form['description'].strip()
        priority = request.form.get('priority', 'Medium')

        image_path = None
        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(
                f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            )
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename

        # Generate unique ticket number
        ticket_no = 'PSR-' + datetime.utcnow().strftime('%Y%m%d%H%M%S')

        req = ServiceRequest(
            ticket_no=ticket_no,
            category=category,
            location=location,
            description=description,
            image_path=image_path,
            priority=priority,
            user_id=current_user.id
        )
        db.session.add(req)
        db.session.commit()
        flash(f'Request submitted! Ticket: {ticket_no}', 'success')
        return redirect(url_for('citizen_dashboard'))

    return render_template('submit_request.html')


# ----- Track Request -----
@app.route('/track/<ticket_no>')
def track_request(ticket_no):
    req = ServiceRequest.query.filter_by(ticket_no=ticket_no).first_or_404()
    return render_template('track_request.html', req=req)


# ----- Admin Dashboard -----
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('citizen_dashboard'))

    all_reqs = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    total = len(all_reqs)
    open_count = sum(1 for r in all_reqs if r.status != 'Resolved')
    resolved = sum(1 for r in all_reqs if r.status == 'Resolved')

    by_category = {}
    for r in all_reqs:
        by_category[r.category] = by_category.get(r.category, 0) + 1

    return render_template('admin_dashboard.html',
                           requests=all_reqs, total=total,
                           open_count=open_count, resolved=resolved,
                           by_category=by_category)


# ----- Update Status -----
@app.route('/admin/update/<int:req_id>', methods=['POST'])
@login_required
def update_status(req_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('citizen_dashboard'))

    req = ServiceRequest.query.get_or_404(req_id)
    new_status = request.form['status']
    req.status = new_status
    req.admin_comment = request.form.get('comment', '').strip()
    db.session.commit()
    flash(f'Request {req.ticket_no} updated to {new_status}.', 'success')
    return redirect(url_for('admin_dashboard'))


# ----- Serve Uploaded Files -----
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ---------- Init DB + Seed Admin ----------
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@egov.com').first():
            admin = User(
                name='Administrator',
                email='admin@egov.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('Default admin created: admin@egov.com / admin123')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)