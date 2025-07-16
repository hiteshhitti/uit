import streamlit as st
import pandas as pd
from db import get_connection
from datetime import date
from utils.helpers import calculate_fine, get_course_completion_status
from utils.helpers import get_unpaid_installments_with_fine

st.title("💰 Fee Management")

conn = get_connection()
cursor = conn.cursor()

# 🔍 Get student list
cursor.execute("SELECT id, name FROM students")
students = cursor.fetchall()
student_dict = {f"{name} (ID: {id})": id for id, name in students}

selected = st.selectbox("Select Student", list(student_dict.keys()))

if selected:
    student_id = student_dict[selected]

    st.markdown("### ❌ Unpaid Installments with Fine")
    unpaid = get_unpaid_installments_with_fine(student_id, conn)

    if unpaid:
        st.dataframe(pd.DataFrame(unpaid))
    else:
        st.success("🎉 No unpaid installments!")

    # 🧾 Get student fee info
    cursor.execute("SELECT final_fee FROM students WHERE id=?", (student_id,))
    total_fee = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount_paid) FROM fees WHERE student_id=?", (student_id,))
    paid = cursor.fetchone()[0] or 0
    remaining = total_fee - paid

    # 🔥 Fine calculation
    fine = calculate_fine(student_id)
    st.warning(f"💸 Current Fine: ₹{fine}")

    # 🎓 Course Completion Status
    course_status = get_course_completion_status(student_id)
    if course_status == "Completed":
        st.success("🎓 Course Status: Completed")
    elif course_status == "Attendance Short":
        st.error("⚠️ Course Status: Attendance Short")
    else:
        st.info("⏳ Course Status: Not Evaluated")

    st.markdown(f"**Total Fee:** ₹{total_fee}")
    st.markdown(f"**Paid Amount:** ₹{paid}")
    st.markdown(f"**Remaining Fee:** ₹{remaining}")

    # 🧾 Show form only if fee is pending
    if remaining <= 0:
        st.success("🎉 Full fee already paid!")
    else:
        st.subheader("➕ Add Installment")
        with st.form("fee_form"):
            amount = st.number_input("Installment Amount", min_value=1, max_value=remaining, step=100)
            payment_date = st.date_input("Payment Date", value=date.today())
            mode = st.selectbox("Payment Mode", ["Cash", "Online", "Cheque", "UPI"])
            remarks = st.text_input("Remarks", placeholder="e.g. 1st Installment")
            pay = st.form_submit_button("Add Payment")

            if pay:
                if amount > remaining:
                    st.error("❌ Amount exceeds remaining fee.")
                else:
                    # Add to fees table
                    cursor.execute("""
                        INSERT INTO fees (student_id, amount_paid, payment_date, mode, remarks)
                        VALUES (?, ?, ?, ?, ?)
                    """, (student_id, amount, payment_date.isoformat(), mode, remarks))

                    # Update fee_schedule if matched
                    cursor.execute("""
                        UPDATE fee_schedule
                        SET is_paid = 1
                        WHERE student_id=? AND due_date=? AND amount_due=?
                    """, (student_id, payment_date.isoformat(), amount))

                    conn.commit()
                    st.success("✅ Payment added successfully!")
                    st.rerun()

    # 📜 Show payment history
    st.subheader("📋 Payment History")
    cursor.execute("""
        SELECT payment_date, amount_paid, mode, remarks
        FROM fees WHERE student_id=? ORDER BY payment_date DESC
    """, (student_id,))
    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=["Date", "Amount", "Mode", "Remarks"])
    st.dataframe(df, use_container_width=True)

conn.close()
