# db.py
import sqlite3

def get_connection():
    return sqlite3.connect("database/student_data.db", check_same_thread=False)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Students Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT,
        gender TEXT,
        contact TEXT NOT NULL,
        aadhar BIGINT,
        address TEXT,
        admission_date TEXT NOT NULL,
        fee_mode VARCHAR(20),
        due_day INTEGER,
        course_id INTEGER NOT NULL,
        discount INTEGER DEFAULT 0,
        final_fee INTEGER NOT NULL,
        status TEXT DEFAULT 'active',  -- 🟢 active / 🔴 deactivated / 🟣 paused
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    """)

    # Fee Exceptions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fee_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        due_month TEXT,
        approved INTEGER DEFAULT 0,
        UNIQUE(student_id, due_month),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    # Fees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount_paid INTEGER,
        payment_date TEXT,
        mode TEXT,
        remarks TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    # Attendance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        status TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    # Fines Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        amount INTEGER,
        reason TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    # Courses Table with duration_months added
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        fee INTEGER,
        duration_months INTEGER
    )
    """)

        # Fee Schedule Table (manual due dates and amount)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fee_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        due_date TEXT,
        amount_due INTEGER,
        remarks TEXT,
        is_paid INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()
