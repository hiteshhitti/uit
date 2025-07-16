import streamlit as st
import pandas as pd
import sqlite3
import os
from db import get_connection
from utils.helpers import apply_auto_fines, check_and_update_leave_status, is_holiday
from datetime import datetime, timedelta

# --- Utility functions ---
def get_setting(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def is_holiday(date):
    if date.weekday() == 6:
        return True  # Sunday
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM holidays WHERE date = ?", (date.strftime("%Y-%m-%d"),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# --- Admin Panel UI ---
st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🛠 Admin Control Panel")

# ✅ Simple Password Protection
admin_pass = st.text_input("Admin Password", type="password")
if admin_pass != "admin123":
    st.warning("Access Denied: Wrong Password")
    st.stop()

st.success("✅ Welcome Admin!")

# 1. ⚙️ Dynamic Settings
st.header("⚙️ Global Settings")
fine_default = int(get_setting("fine_amount", 100))
fine = st.number_input("Default Fine per Day (₹)", value=fine_default, step=10)

pause_threshold_default = int(get_setting("pause_after_leave_days", 20))
pause_days = st.number_input("Leave Days for Pause", value=pause_threshold_default, step=1)

if st.button("💾 Save Settings"):
    set_setting("fine_amount", str(fine))
    set_setting("pause_after_leave_days", str(pause_days))
    st.success("✅ Settings saved successfully!")

# 2. 🔁 Trigger Backend Logic
st.header("🔁 Trigger Backend Scripts")
col1, col2 = st.columns(2)
with col1:
    if st.button("💸 Apply Auto Fines Now"):
        apply_auto_fines()
        st.success("Fines Applied")
with col2:
    if st.button("🔄 Update Leave Statuses"):
        check_and_update_leave_status()
        st.success("Statuses Updated")

# 3. 📥 Bulk Import
st.header("📥 Bulk Student Upload")
csv_file = st.file_uploader("Upload CSV File", type=["csv"])
if csv_file:
    df = pd.read_csv(csv_file)
    st.dataframe(df.head())
    if st.button("📤 Import to Database"):
        conn = get_connection()
        cursor = conn.cursor()
        imported = 0
        for _, row in df.iterrows():
            cursor.execute("SELECT id FROM courses WHERE name = ?", (row['course_name'],))
            course = cursor.fetchone()
            if not course:
                continue
            cursor.execute("""
                INSERT INTO students (name, dob, gender, contact, aadhar, address, admission_date,
                                      fee_mode, due_day, course_id, discount, final_fee, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                row['name'], row['dob'], row['gender'], row['contact'], row['aadhar'], row['address'],
                row['admission_date'], row['fee_mode'], row['due_day'], course[0],
                row['discount'], row['final_fee']
            ))
            imported += 1
        conn.commit()
        conn.close()
        st.success(f"✅ Imported {imported} students")



# 4. 🧾 Student ID List Viewer
conn = get_connection()
cursor = conn.cursor()
st.header("🧾 Student ID List Viewer")
cursor.execute("SELECT id, name, contact, admission_date FROM students ORDER BY id")
students = cursor.fetchall()
if students:
    st.subheader("📋 All Students with IDs")
    df_ids = pd.DataFrame(students, columns=["ID", "Name", "Contact", "Admission Date"])
    df_ids["Admission Date"] = pd.to_datetime(df_ids["Admission Date"]).dt.strftime("%d-%b-%Y")
    st.dataframe(df_ids, use_container_width=True)
    csv = df_ids.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Student ID List", csv, file_name="student_id_list.csv", key="student_id_download")
else:
    st.info("No students found in database.")

# 5. 📅 Holiday Manager
cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        date TEXT PRIMARY KEY,
        reason TEXT,
        manual INTEGER DEFAULT 0
    )
""")

holiday_date = st.date_input("Select Holiday Date")
holiday_reason = st.text_input("Holiday Reason")

if st.button("➕ Mark Manual Holiday"):
    cursor.execute("REPLACE INTO holidays (date, reason, manual) VALUES (?, ?, 1)", (holiday_date.isoformat(), holiday_reason))
    conn.commit()
    st.success("✅ Holiday marked manually!")

# Automatically mark all Sundays if not already in table
cursor.execute("SELECT date FROM holidays WHERE reason = 'Sunday'")
existing = {row[0] for row in cursor.fetchall()}

today = datetime.today()
cursor.execute("SELECT MIN(admission_date) FROM students")
admission_start = cursor.fetchone()[0]
if admission_start:
    start_year = datetime.strptime(admission_start, "%Y-%m-%d").year
else:
    start_year = today.year

start = datetime(start_year, 1, 1)
end = datetime(today.year + 3, 12, 31)  # Covers future Sunday holidays too
day = start
while day <= end:
    if day.weekday() == 6:  # Sunday
        ds = day.strftime("%Y-%m-%d")
        if ds not in existing:
            cursor.execute("INSERT OR IGNORE INTO holidays (date, reason, manual) VALUES (?, 'Sunday', 0)", (ds,))
    day += timedelta(days=1)

conn.commit()

cursor.execute("SELECT date, reason, manual FROM holidays ORDER BY date DESC")
holidays = cursor.fetchall()
conn.close()

if holidays:
    st.subheader("📋 Existing Holidays")
    df = pd.DataFrame(holidays, columns=["Date", "Reason", "Manual"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d-%b-%Y")
    df["Type"] = df["Manual"].apply(lambda x: "Manual" if x else "Auto")
    df.drop(columns=["Manual"], inplace=True)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No holidays added yet.")
