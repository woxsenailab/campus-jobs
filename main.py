import os
import sqlite3
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

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, email):
        self.email = email

    def get_id(self):
        return self.email

# Define Student class inheriting from User
class Student(User):
    def __init__(self, email, password):
        super().__init__(email)
        self.password = password

    @staticmethod
    def get(email):
        conn = sqlite3.connect('pdfs.db')
        c = conn.cursor()

        c.execute('SELECT Email_ID, Password FROM students WHERE Email_ID = ?', (email,))
        user_data = c.fetchone()
        conn.close()

        if user_data:
            return Student(user_data[0], user_data[1])
        else:
            return None

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

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    user = Faculty.get(user_id)
    if not user:
        user = Student.get(user_id)
    return user

CORS(app)

def init_db():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            Email_ID TEXT PRIMARY KEY,
            Password TEXT NOT NULL
        );
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            Email_ID TEXT PRIMARY KEY,
            Password TEXT NOT NULL
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            description TEXT,
            pdf_path TEXT
        );
    """)


    c.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            applicant_email TEXT NOT NULL,
            UNIQUE(job_id, applicant_email),
            FOREIGN KEY (job_id) REFERENCES job(id)
        );
    """)

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE Email_ID = ? AND Password = ?", (email, password))
    user = c.fetchone()

    if not user:
        c.execute("SELECT * FROM students WHERE Email_ID = ? AND Password = ?", (email, password))
        user = c.fetchone()

        if user:
            session['email'] = email
            conn.close()
            return jsonify({'redirect': url_for('student_dashboard')})

    if user:
        conn.close()
        return jsonify({'redirect': url_for('faculty_dashboard')})
    else:
        error = 'Invalid email or password. Please try again.'
        conn.close()
        return jsonify({'error': error})

@app.route('/logout')
def logout():
    logout_user()
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
    print(data)
    file_type = data.get('type')
    course = data.get('course')
    semester = data.get('semester')   
    specialization = data.get('specialization')
    #specialization = 'MBA_GEN'
    directory = os.path.join(app.config['UPLOAD_FOLDER'], file_type)

    if file_type == 'TT':
        if specialization == 'MBA_GEN':
            section = data.get('section')
            filename = f"{file_type}_{course}_{semester}_{specialization}_{section}.pdf"
        elif specialization in ['MBA FS','MBA BA']:
            filename = f"{file_type}_{course}_{semester}_{specialization}.pdf"
    elif file_type in ['CO', 'AS']:
        subject = data.get('subject').replace(' ', '_')
        if specialization == 'MBA_GEN':
            section = data.get('section')            
            filename = f"{file_type}_{course}_{semester}_{specialization}_{section}_{subject}.pdf"
        elif specialization in ['MBA FS','MBA BA']:
            filename = f"{file_type}_{course}_{semester}_{specialization}_{subject}.pdf"
    else:
        return jsonify({'message': 'Invalid file type'}), 400

    file_path = os.path.join(directory, filename)

    if os.path.exists(file_path):
        return send_from_directory(directory, filename)
    else:
        return jsonify({'message': f'{file_type} file not found for the specified course, semester, and section'}), 404
    
@app.route('/post_job')
def post_job():
    return render_template('Post_job.html')

@app.route('/submit_job', methods=['POST'])
def submit_job():
    department = request.form['department']
    designation = request.form['designation']
    description = request.form['description']
    pdf = request.files['pdf']

    if not all([department, designation, description, pdf]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Save the uploaded PDF file
    if pdf:
        filename = secure_filename(pdf.filename)
        pdf_path = os.path.join(app.config['PDF_UPLOAD_FOLDER'], filename)
        pdf.save(pdf_path)

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('INSERT INTO job (department, designation, description, pdf_path) VALUES (?, ?, ?, ?)',
              (department, designation, description, pdf_path))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Job Posted Successfully!'}), 200

@app.route('/faculty_dashboard')
def faculty_dashboard():
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job')
    jobs = c.fetchall()

    job_list = []
    for job in jobs:
        job_dict = {
            'id': job[0],
            'department': job[1],
            'designation': job[2],
            'description': job[3],
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
def student_dashboard():
    email = session.get('email')

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()

    c.execute('SELECT * FROM job')
    jobs = c.fetchall()

    conn.close()

    return render_template('Student.html', email=email, jobs=jobs) 

@app.route('/Edit_job')
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
    department = request.form.get('department')
    designation = request.form.get('designation')
    description = request.form.get('description')
    pdf = request.files.get('pdf')

    if not all([department, designation, description]):
        return jsonify({'message': 'Missing required fields'}), 400

    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()
    c.execute('SELECT id, pdf_path FROM job WHERE id = ?', (job_id,))
    existing_job = c.fetchone()

    if existing_job:
        if pdf:
            filename = secure_filename(pdf.filename)
            pdf_path = os.path.join(app.config['PDF_UPLOAD_FOLDER'], filename)
            pdf.save(pdf_path)
            c.execute('UPDATE job SET department = ?, designation = ?, description = ?, pdf_path = ? WHERE id = ?',
                      (department, designation, description, pdf_path, job_id))
        else:
            c.execute('UPDATE job SET department = ?, designation = ?, description = ? WHERE id = ?',
                      (department, designation, description, job_id))

        conn.commit()
        conn.close()
        return jsonify({'message': f'Job with ID {job_id} updated successfully', 'success': True}), 200
    else:
        conn.close()
        return jsonify({'message': f'Job with ID {job_id} does not exist'}), 404



@app.route('/api/delete_job/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    conn = sqlite3.connect('pdfs.db')
    c = conn.cursor()
    c.execute('SELECT id FROM job WHERE id = ?', (job_id,))
    existing_job = c.fetchone()

    if existing_job:
        c.execute('DELETE FROM job WHERE id = ?', (job_id,))
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
