import streamlit as st
import pandas as pd
from db import get_connection
from datetime import date
from utils.helpers import update_student_status
from utils.helpers import update_student_status, is_holiday

st.title("📆 Attendance Management")

conn = get_connection()
cursor = conn.cursor()

# 🗓️ Select Date First
att_date = st.date_input("Select Date", value=date.today())


if is_holiday(att_date):
    st.warning("🚫 This is a holiday. Attendance cannot be marked.")
    st.stop()
    
# 🔍 Fetch only eligible students (admitted on or before selected date)
cursor.execute("""
    SELECT id, name FROM students
    WHERE admission_date <= ?
""", (att_date.isoformat(),))
students = cursor.fetchall()

if not students:
    st.warning("⚠️ No students were admitted on or before this date.")
    conn.close()
    st.stop()

# ✅ Create dropdown for valid students
student_dict = {f"{name} (ID: {id})": id for id, name in students}
selected = st.selectbox("Select Student", list(student_dict.keys()))

if selected:
    student_id = student_dict[selected]

    # ✅ Show student status with color (safe fetch)
    cursor.execute("SELECT status FROM students WHERE id=?", (student_id,))
    row = cursor.fetchone()
    if not row:
        st.error("❌ Student not found.")
        conn.close()
        st.stop()

    current_status = row[0]
    status_color = {
        "active": "green",
        "deactivated": "red",
        "paused": "purple"
    }
    color = status_color.get(current_status, "gray")
    label = current_status.upper() if isinstance(current_status, str) else str(current_status)
    st.markdown(f"**ID Status:** :{color}[{label}]")

    # 🗓️ Mark attendance
    cursor.execute("SELECT status FROM attendance WHERE student_id=? AND date=?", (student_id, att_date.isoformat()))
    existing = cursor.fetchone()

    if existing:
        st.warning(f"⚠️ Attendance already marked as '{existing[0]}' for this date.")
    else:
        att_status = st.radio("Mark Attendance", ["Present", "Absent", "Leave"], index=0)
        if st.button("Save Attendance"):
            cursor.execute("""
                INSERT INTO attendance (student_id, date, status)
                VALUES (?, ?, ?)
            """, (student_id, att_date.isoformat(), att_status))
            conn.commit()

            update_student_status(student_id)
            st.success(f"✅ Attendance marked as {att_status}!")

    # 📊 Attendance history
    st.subheader("📅 Attendance History")
    cursor.execute("""
        SELECT date, status FROM attendance
        WHERE student_id=?
        ORDER BY date DESC
    """, (student_id,))
    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=["Date", "Status"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%d-%b-%Y')
    st.dataframe(df, use_container_width=True)

conn.close()
