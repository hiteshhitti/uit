# pages/7_Set_Fee_Due_Dates.py
import streamlit as st
from db import get_connection
from datetime import date
import pandas as pd

st.title("🗓️ Set Fee Due Dates Manually")

conn = get_connection()
cursor = conn.cursor()

# Get student list
cursor.execute("SELECT id, name FROM students")
students = cursor.fetchall()
student_dict = {f"{name} (ID: {id})": id for id, name in students}

selected = st.selectbox("Select Student", list(student_dict.keys()))

if selected:
    student_id = student_dict[selected]

    st.subheader("➕ Add Installment Due Date")

    with st.form("due_form"):
        due_date = st.date_input("Due Date", value=date.today())
        amount = st.number_input("Installment Amount", min_value=100, step=100)
        remarks = st.text_input("Remarks (Optional)")
        submit = st.form_submit_button("Add Due Date")

        if submit:
            cursor.execute("""
                INSERT INTO fee_schedule (student_id, due_date, amount_due, remarks)
                VALUES (?, ?, ?, ?)
            """, (student_id, due_date.isoformat(), amount, remarks))
            conn.commit()
            st.success("✅ Due date added.")

    # Show existing due schedule
    st.subheader("📋 Existing Due Dates")
    cursor.execute("""
        SELECT due_date, amount_due, is_paid, remarks
        FROM fee_schedule
        WHERE student_id=?
        ORDER BY due_date
    """, (student_id,))
    rows = cursor.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["Due Date", "Amount", "Paid", "Remarks"])
        df["Paid"] = df["Paid"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No due dates added yet.")

conn.close()
