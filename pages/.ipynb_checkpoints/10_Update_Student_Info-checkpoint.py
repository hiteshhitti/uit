import streamlit as st
import pandas as pd
from db import get_connection

st.title("Update Student Info")

conn = get_connection()
cursor = conn.cursor()

# 🔍 Fetch all students
cursor.execute("SELECT id, name FROM students ORDER BY name")
students = cursor.fetchall()
student_map = {f"{name} (ID: {id})": id for id, name in students}

# Add a default option to avoid KeyError
selected = st.selectbox("Select Student", ["-- Select --"] + list(student_map.keys()))

# ✅ Only proceed if student is selected
if selected != "-- Select --":
    student_id = student_map[selected]

    # 📋 Fetch current data
    cursor.execute("""
        SELECT name, dob, gender, contact, aadhar, address, discount, final_fee
        FROM students WHERE id=?
    """, (student_id,))
    record = cursor.fetchone()

    name, dob, gender, contact, aadhar, address, discount, final_fee = record

    # 📝 Editable Form
    with st.form("update_form"):
        new_name = st.text_input("Name", value=name)
        new_dob = st.date_input("Date of Birth", value=pd.to_datetime(dob))
        new_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(gender))
        new_contact = st.text_input("Contact", value=contact)
        new_aadhar = st.text_input("Aadhar Number", value=str(aadhar) if aadhar else "")
        new_address = st.text_area("Address", value=address)
        new_discount = st.number_input("Discount (₹)", min_value=0, step=100, value=discount)
        new_final_fee = st.number_input("Final Fee (₹)", min_value=0, step=500, value=final_fee)

        submit = st.form_submit_button("✅ Update Info")
        if submit:
            cursor.execute("""
                UPDATE students SET name=?, dob=?, gender=?, contact=?, aadhar=?, address=?, discount=?, final_fee=?
                WHERE id=?
            """, (
                new_name, new_dob.strftime("%Y-%m-%d"), new_gender, new_contact, new_aadhar,
                new_address, new_discount, new_final_fee, student_id
            ))
            conn.commit()
            st.success("🎉 Student info updated successfully!")

conn.close()
