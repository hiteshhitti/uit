import streamlit as st
from db import get_connection
from datetime import date
from utils.helpers import update_student_status

st.title("🧑‍🤝‍🧑 Mass Attendance Entry")

conn = get_connection()
cursor = conn.cursor()

# 📅 Select Date
att_date = st.date_input("Select Attendance Date", value=date.today())

# 👥 Get all active students
cursor.execute("""
    SELECT id, name FROM students
    WHERE status='active' AND admission_date <= ?
""", (att_date.isoformat(),))
students = cursor.fetchall()


if not students:
    st.info("No active students to mark attendance.")
    conn.close()
    st.stop()

# 📋 Attendance form
with st.form("mass_attendance_form"):
    st.write("### Mark Attendance")

    attendance_data = {}
    skipped = 0

    for student_id, name in students:
        cursor.execute("""
            SELECT status FROM attendance WHERE student_id=? AND date=?
        """, (student_id, att_date.isoformat()))
        existing = cursor.fetchone()

        if existing:
            # 🔒 Already marked — show as disabled text
            st.markdown(f"❌ **{name} (ID: {student_id})** – Already marked as `{existing[0]}`")
            skipped += 1
        else:
            # ✅ Mark new attendance
            status = st.selectbox(
                f"{name} (ID: {student_id})",
                ["Present", "Absent", "Leave"],
                key=f"status_{student_id}"
            )
            attendance_data[student_id] = status

    submit = st.form_submit_button("✅ Save All Attendance")

if submit:
    inserted = 0
    for student_id, status in attendance_data.items():
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status)
            VALUES (?, ?, ?)
        """, (student_id, att_date.isoformat(), status))
        update_student_status(student_id)
        inserted += 1

    conn.commit()
    st.success(f"✅ Attendance saved for {inserted} students.")
    if skipped:
        st.warning(f"⚠️ {skipped} students already had attendance marked and were skipped.")

conn.close()
