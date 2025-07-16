import streamlit as st
from db import get_connection
from datetime import datetime

st.title("✅ Approve Late Fee Waiver")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM students")
students = cursor.fetchall()
student_dict = {f"{name} (ID: {id})": id for id, name in students}

selected = st.selectbox("Select Student", list(student_dict.keys()))
month = st.text_input("Month (YYYY-MM) for Waiver", value=datetime.today().strftime("%Y-%m"))

if st.button("Approve Exception"):
    cursor.execute("""
        INSERT INTO fee_exceptions (student_id, due_month, approved)
        VALUES (?, ?, 1)
        ON CONFLICT(student_id, due_month) DO UPDATE SET approved=1
    """, (student_dict[selected], month))
    conn.commit()
    st.success("✅ Waiver Approved")

conn.close()
