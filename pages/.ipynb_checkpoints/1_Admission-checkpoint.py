import streamlit as st
from db import get_connection

st.title("📝 Student Admission")

conn = get_connection()
cursor = conn.cursor()

# Fetch courses for dropdown
cursor.execute("SELECT id, name, fee, duration_months FROM courses")
courses = cursor.fetchall()

if not courses:
    st.warning("Please add courses first in Course Manager.")
    conn.close()
    st.stop()

# Admission Form
with st.form("admission_form"):
    name = st.text_input("Student Name").strip()
    dob = st.date_input("Date of Birth (optional)")
    gender = st.radio("Gender", ["Male", "Female", "Other"])
    contact = st.text_input("Contact Number (10 digits)").strip()
    aadhar = st.text_input("Aadhar Number (optional)").strip()
    address = st.text_area("Address")
    admission_date = st.date_input("Admission Date")
    due_day = st.number_input("Fee Due Day (1-28)", min_value=1, max_value=28, step=1)

    course_names = [f"{name} (₹{fee}) - {duration} months" for _, name, fee, duration in courses]
    selected_course = st.selectbox("Select Course", course_names)
    course_index = course_names.index(selected_course)
    course_id, _, course_fee, course_duration = courses[course_index]

    discount = st.number_input("Discount (if any)", min_value=0, value=0, step=100)
    final_fee = course_fee - discount

    st.markdown(f"**Final Fee Payable: ₹{final_fee}**")

    # ================= Manual Fee Installment Section ===================
    st.markdown("### 💸 Fee Installment Plan")

    if "installment_rows" not in st.session_state:
        st.session_state.installment_rows = 1

    rows = st.session_state.installment_rows
    installments = []

    for i in range(rows):
        col1, col2 = st.columns(2)
        amount = col1.number_input(f"Installment {i+1} Amount", min_value=0, key=f"amount_{i}")
        due_date = col2.date_input(f"Installment {i+1} Due Date", key=f"due_date_{i}")
        installments.append((amount, due_date))

    if st.form_submit_button("➕ Add Another Installment"):
        st.session_state.installment_rows += 1
        st.rerun()

    submitted = st.form_submit_button("📥 Submit Admission")

    if submitted:
        # Save student
        cursor.execute("""
            INSERT INTO students (name, dob, gender, contact, aadhar, address, admission_date,
                                  due_day, course_id, discount, final_fee, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, dob.strftime("%Y-%m-%d"), gender, contact,
            aadhar if aadhar else None, address,
            admission_date.strftime("%Y-%m-%d"),
            due_day, course_id, discount, final_fee, "active"
        ))

        conn.commit()
        student_id = cursor.lastrowid

        # Save Fee Installment Schedule
        for amount, due_date in installments:
            cursor.execute("""
                INSERT INTO fee_schedule (student_id, due_date, amount_due)
                VALUES (?, ?, ?)
            """, (student_id, due_date.strftime("%Y-%m-%d"), amount))

        conn.commit()
        conn.close()

        st.success("Student admitted and fee schedule saved successfully.")
