import streamlit as st
from db import get_connection

st.title("📋 Student List")

conn = get_connection()
cursor = conn.cursor()

# Fetch all students with course name
cursor.execute("""
    SELECT s.id, s.name, s.gender, s.contact, s.admission_date, s.status, c.name as course_name
    FROM students s
    JOIN courses c ON s.course_id = c.id
""")
students = cursor.fetchall()

# Categorize by status
active_students = [s for s in students if s[5] == 'active']
paused_students = [s for s in students if s[5] == 'paused']
deactivated_students = [s for s in students if s[5] == 'deactivated']

# 🟢 Active Students
st.subheader("🟢 Active Students")
if not active_students:
    st.info("No active students.")
else:
    for student_id, name, gender, contact, admission_date, status, course_name in active_students:
        with st.expander(f"🧑‍🎓 {name} | 📞 {contact}"):
            st.markdown(f"""
**Gender:** {gender}  
**Admission Date:** {admission_date}  
**Course:** {course_name}  
**Status:** `{status}`
            """)

# 🟣 Paused Students
st.markdown("---")
with st.expander("🟣 Paused Students"):
    if not paused_students:
        st.info("No paused students.")
    else:
        for student_id, name, gender, contact, admission_date, status, course_name in paused_students:
            col1, col2 = st.columns([4, 1])
            with col1:
                with st.expander(f"🔄 {name} | 📞 {contact}"):
                    st.markdown(f"""
**Gender:** {gender}  
**Admission Date:** {admission_date}  
**Course:** {course_name}  
**Status:** `{status}`
                    """)
            with col2:
                if st.button("▶️ Resume", key=f"resume_{student_id}"):
                    cursor.execute("UPDATE students SET status = 'active' WHERE id = ?", (student_id,))
                    conn.commit()
                    st.success(f"{name} resumed successfully! Please refresh to see changes.")

# 🔴 Deactivated Students
st.markdown("---")
with st.expander("🔴 Deactivated Students"):
    if not deactivated_students:
        st.info("No deactivated students.")
    else:
        for student_id, name, gender, contact, admission_date, status, course_name in deactivated_students:
            with st.expander(f"🚫 {name} | 📞 {contact}"):
                st.markdown(f"""
**Gender:** {gender}  
**Admission Date:** {admission_date}  
**Course:** {course_name}  
**Status:** `{status}`
                """)

conn.close()
