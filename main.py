import os
import sqlite3
import re
from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PDF_UPLOAD_FOLDER'] = 'static/uploads/'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CORS
CORS(app)

# Function to initialize database
def init_db():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    # Create users table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            Email_ID TEXT PRIMARY KEY,
            Password TEXT NOT NULL
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS job (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id INTEGER NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            description TEXT,
            pdf_path TEXT,
            pdf_filename TEXT
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            applicant_email TEXT NOT NULL,
            UNIQUE(job_id, applicant_email),
            FOREIGN KEY (job_id) REFERENCES job(Job_id)
        );
    """)

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, email):
        self.email = email

    def get_id(self):
        return self.email

# Define Faculty class inheriting from User
class Faculty(User):
    @staticmethod
    def get(email):
        conn = sqlite3.connect('pdfs.db')
        c = conn.cursor()
        c.execute('SELECT Email_ID, Password FROM users WHERE Email_ID = ?', (email,))
        user_data = c.fetchone()
        conn.close()

        if user_data:
            return Faculty(user_data[0])
        else:
            return None

# Define Student class inheriting from User
class Student(User):
    @staticmethod
    def get(email):
        if re.match(r'^[^@]+@woxsen\.edu\.in$', email):
            return Student(email)
        else:
            return None

# Flask-Login user loader for Faculty and Student
@login_manager.user_loader
def load_user(user_id):
    user = Faculty.get(user_id)
    if not user:
        user = Student.get(user_id)
    return user


# Route for home page
@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/stud_log')
def stud_log():
    return render_template('Student_login.html')

@app.route('/faculty_log')
def faculty_log():
    return render_template('Faculty_login.html')


@app.route('/login', methods=['POST'])
def login():
    login_type = request.form.get('login_type')

    if login_type == 'faculty':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('pdfs.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE Email_ID = ? AND Password = ?", (email, password))
        user = c.fetchone()

        if user:
            user_obj = Faculty.get(email)
            login_user(user_obj)
            conn.close()
            return jsonify({'redirect': url_for('faculty_dashboard')})
        else:
            error = 'Invalid email or password. Please try again.'
            conn.close()
            return jsonify({'error': error})

    elif login_type == 'student':
        email = request.form.get('email')

        if not email:
            error = 'Email is required.'
            return jsonify({'error': error})

        student = Student.get(email)

        if student:
            login_user(student)
            session['email'] = email
            return jsonify({'redirect': url_for('student_dashboard')})
        else:
            error = 'Invalid email. Please provide valid email.'
            return jsonify({'error': error})

    else:
        error = 'Invalid login type.'
        return jsonify({'error': error})

# Route for logout
@app.route('/logout')
def logout():
    logout_user()  
    session.pop('email', None) 
    return render_template('Home.html')

@app.route('/api/upload', methods=['POST'])
def upload_Documents():
    if 'pdf' not in request.files:
        return 'no selected file',400
    
    files = request.files.getlist('pdf')

    for file in files: 
        filename = secure_filename(file.filename)
        print(filename)
        if 'TT' in filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],'TT', filename))
            return jsonify({'message': ' TT file Uploaded successsfuly '}) 
        elif 'CO' in filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],'CO', filename))
            return jsonify({'message': ' CO file Uploaded successsfuly '}) 
        elif 'AS' in filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],'AS', filename))
            return jsonify({'message': ' AS file Uploaded successsfuly '}) 

@app.route('/api/view_files', methods=['POST'])
def view_files():
    data = request.get_json()
    file_type = data.get('type')
    course = data.get('course')
    semester = data.get('semester').replace(' ', '_')
    section = data.get('section')
    subject = data.get('subject')

    directory = os.path.join(app.config['UPLOAD_FOLDER'], file_type)

    if file_type == 'TT':
        filename = f"{file_type}{course}{semester}_{section}.pdf"
    elif file_type in ['CO', 'AS']:
        filename = f"{file_type}{course}{semester}{section}{subject}.pdf"
    else:
        return jsonify({'message': 'Invalid file type'}), 400

    file_path = os.path.join(directory, filename)

    if os.path.exists(file_path):
        return send_from_directory(directory, filename)
    else:
        return jsonify({'message': f'{file_type} file not found for the specified course, semester, and section'}), 404
    
@app.route('/post_job')
@login_required
def post_job():
    return render_template('Post_job.html')

@app.route('/submit_job', methods=['POST'])
@login_required
def submit_job():
    job_id = request.form['job_id']
    department = request.form['department']
    designation = request.form['designation']
    description = request.form['description']
    pdf = request.files['pdf']

    if not all([job_id, department, designation, description, pdf]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Save the uploaded PDF file
    if pdf:
        filename = secure_filename(pdf.filename)
        pdf_path = os.path.join(app.config['PDF_UPLOAD_FOLDER'], filename)
        pdf.save(pdf_path)

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('INSERT INTO job (id, department, designation, description, pdf_path, pdf_filename) VALUES (?, ?, ?, ?, ?, ?)',
              (job_id, department, designation, description, pdf_path, filename))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Job Posted Successfully!'}), 200

@app.route('/api/jobs_list')
def jobs_list():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job')
    jobs = c.fetchall()
    job_list = []
    for job in jobs:
        job_dict = {
            'id': job[1],
            'department': job[2],
            'designation': job[3],
            'document_path':job[5],
            'filename': job[6]
        }
        job_list.append(job_dict)

    conn.close()

    return job_list

@app.route('/faculty_dashboard')
@login_required
def faculty_dashboard():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job')
    jobs = c.fetchall()

    job_list = []
    for job in jobs:
        job_dict = {
            'Job_id': job[0],
            'id': job[1],
            'department': job[2],
            'designation': job[3],
            'description': job[4],
            'applicants': []
        }

        c.execute('SELECT applicant_email FROM job_applications WHERE job_id = ?', (job[0],))
        applicants = c.fetchall()
        job_dict['applicants'] = [applicant[0] for applicant in applicants]
        job_dict['num_applicants'] = len(applicants)  

        job_list.append(job_dict)

    conn.close()

    return render_template('Faculty.html', jobs=job_list)

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if 'email' in session:
        email = session['email']

        conn = sqlite3.connect('pdfs.db')
        c = conn.cursor()

        c.execute('SELECT * FROM job')
        jobs = c.fetchall()

        conn.close()

        return render_template('Student.html', email=email, jobs=jobs)
    else:
        return jsonify({'message': 'Session email not found. Please log in again.'}), 404


@app.route('/Edit_job')
@login_required
def Edit_job():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job')
    jobs = c.fetchall()

    conn.close()
    return render_template('Edit_job.html', jobs=jobs) 

@app.route('/pdfs/<path:pdf_path>')
def view_pdf(pdf_path):
    pdf_directory = app.config['PDF_UPLOAD_FOLDER']
    if not os.path.exists(os.path.join(pdf_directory, pdf_path)):
        return jsonify({'message': 'PDF file not found'}), 404
    return send_from_directory(pdf_directory, pdf_path)


@app.route('/api/edit_job/<int:job_id>', methods=['POST'])
def edit_job(job_id):
    new_job_id = request.form.get('id')
    department = request.form.get('department')
    designation = request.form.get('designation')
    description = request.form.get('description')
    pdf = request.files.get('pdf')
    filename = secure_filename(pdf.filename) if pdf else None

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job WHERE job_id = ?', (job_id,))
    job = c.fetchone()
    
    if job:
        if pdf:
            pdf_filename = filename
        else:
            pdf_filename = job[6]  

        c.execute('UPDATE job SET id = ?, department = ?, designation = ?, description = ?, pdf_filename = ? WHERE job_id = ?',
                  (new_job_id, department, designation, description, pdf_filename, job_id))

        if pdf:
            pdf_path = os.path.join(app.config['PDF_UPLOAD_FOLDER'], filename)
            pdf.save(pdf_path)
            c.execute('UPDATE job SET pdf_path = ? WHERE job_id = ?', (pdf_path, job_id))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'pdf_filename': pdf_filename}), 200
    else:
        conn.close()
        return jsonify({'success': False, 'error': 'Job not found'}), 404




@app.route('/api/delete_job/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()
    c.execute('SELECT Job_id FROM job WHERE Job_id = ?', (job_id,))
    existing_job = c.fetchone()

    if existing_job:
        c.execute('DELETE FROM job WHERE Job_id = ?', (job_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Job with ID {job_id} deleted successfully', 'success': True}), 200
    else:
        conn.close()
        return jsonify({'message': f'Job with ID {job_id} does not exist', 'success': False}), 404


@app.route('/apply_job/<int:job_id>', methods=['POST'])
def apply_for_job(job_id):
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'message': 'Email not provided.'}), 400

        conn = sqlite3.connect('pdfs.db')
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM job_applications WHERE job_id = ? AND applicant_email = ?", (job_id, email))
            existing_application = c.fetchone()

            if existing_application:
                return jsonify({'message': 'You have already applied for this job.'}), 400

            c.execute("INSERT INTO job_applications (job_id, applicant_email) VALUES (?, ?)", (job_id, email))
            conn.commit()

            return jsonify({'message': 'Application submitted successfully!', 'success': True}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'message': str(e)}), 500
        finally:
            conn.close()

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=8000, debug=True)
