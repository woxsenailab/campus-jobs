import sqlite3

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('data.db')
    return conn

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            ID INTEGER PRIMARY KEY,
            Email_ID TEXT NOT NULL,
            Password INTEGER NOT NULL,
            Section TEXT
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            Email_ID TEXT PRIMARY KEY,
            Password INTEGER NOT NULL,
            Course TEXT NOT NULL,
            Semester TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            section TEXT NOT NULL,
            file BLOB NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_outline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            sec TEXT,
            subject TEXT NOT NULL,
            file BLOB NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            sec TEXT,
            subject TEXT NOT NULL,
            file BLOB NOT NULL
        );
    """)
    
    conn.commit()
    conn.close()

def add_users(Id, EmailID, PassW, Sec):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO users (ID, Email_ID, Password, Section) VALUES (?, ?, ?, ?)"
    values = (Id, EmailID, PassW, Sec)
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

def add_student(Emailid, Pass, course, section):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO students (Email_ID, Password, Course, Semester) VALUES (?, ?, ?, ?)"
    values = (Emailid, Pass, course, section)
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

def add_timetable(TCour, Tsem, Tsec, Tfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO timetable (course, semester, section, file) VALUES (?, ?, ?, ?)"
    values = (TCour, Tsem, Tsec, Tfile)
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

def add_courseoutline(CCour, Csem, Csec, Csubject, Cfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO course_outline (course, semester, sec, subject, file) VALUES (?, ?, ?, ?, ?)"
    values = (CCour, Csem, Csec, Csubject, Cfile)
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

def add_assignment(ACour, Asem, Asec, Asub, Afile):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO assignment (course, semester, sec, subject, file) VALUES (?, ?, ?, ?, ?)"
    values = (ACour, Asem, Asec, Asub, Afile)
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

create_tables()
