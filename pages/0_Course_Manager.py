import streamlit as st
from db import get_connection

st.title("📚 Course Manager")

conn = get_connection()
cursor = conn.cursor()

st.subheader("➕ Add New Course")

with st.form("course_form"):
    name = st.text_input("Course Name")
    fee = st.number_input("Base Fee (₹)", min_value=0, step=500)
    duration = st.number_input("Course Duration (in months)", min_value=1, step=1)
    submit = st.form_submit_button("Add Course")
    if submit:
        try:
            cursor.execute("INSERT INTO courses (name, fee, duration_months) VALUES (?, ?, ?)", (name, fee, duration))
            conn.commit()
            st.success("✅ Course added successfully!")
        except:
            st.error("❌ Course already exists.")

st.subheader("📋 Existing Courses")

cursor.execute("SELECT name, fee FROM courses")
data = cursor.fetchall()

if data:
    for name, fee in data:
        st.write(f"🔸 **{name}** – ₹{fee}")
else:
    st.info("No courses added yet.")

conn.close()
