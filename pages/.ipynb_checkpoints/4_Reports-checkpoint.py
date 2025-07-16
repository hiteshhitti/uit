# pages/4_Reports.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from db import get_connection

st.title("📊 Reports & Graphs")
conn = get_connection()

# ----- 1. 📈 Admission Trend -----
st.subheader("📈 Monthly Admission Trend")

df_admission = pd.read_sql_query("SELECT admission_date FROM students", conn)
if not df_admission.empty:
    df_admission["admission_date"] = pd.to_datetime(df_admission["admission_date"])
    df_admission["Month"] = df_admission["admission_date"].dt.to_period("M").astype(str)
    monthly_counts = df_admission["Month"].value_counts().sort_index()

    fig1, ax1 = plt.subplots()
    monthly_counts.plot(kind="bar", ax=ax1, color="orange")
    ax1.set_title("Admissions Per Month")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Number of Students")
    fig1.tight_layout()
    st.pyplot(fig1)
else:
    st.info("No admissions found.")

# ----- 2. 💰 Fee Collection Trend -----
st.subheader("💰 Monthly Fee Collection")

df_fees = pd.read_sql_query("SELECT payment_date, amount_paid FROM fees", conn)
if not df_fees.empty:
    df_fees["payment_date"] = pd.to_datetime(df_fees["payment_date"])
    df_fees["Month"] = df_fees["payment_date"].dt.to_period("M").astype(str)
    fee_per_month = df_fees.groupby("Month")["amount_paid"].sum().sort_index()

    fig2, ax2 = plt.subplots()
    fee_per_month.plot(kind="bar", ax=ax2, color="green")
    ax2.set_title("Fee Collected Per Month")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Amount Collected (₹)")
    fig2.tight_layout()
    st.pyplot(fig2)
else:
    st.info("No fee records found.")

# ----- 3. 📊 Attendance Summary -----
st.subheader("📊 Attendance Summary")

df_att = pd.read_sql_query("SELECT status FROM attendance", conn)
if not df_att.empty:
    summary = df_att["status"].value_counts()

    # Dynamically assign colors to status
    color_map = {
        "Present": "#4CAF50",   # Green
        "Absent": "#F44336",    # Red
        "Leave": "#2196F3"      # Blue
    }
    colors = [color_map.get(status, "#9E9E9E") for status in summary.index]

    fig3, ax3 = plt.subplots()
    ax3.pie(summary, labels=summary.index, autopct="%1.1f%%", colors=colors)
    ax3.set_title("Overall Attendance")
    fig3.tight_layout()
    st.pyplot(fig3)
else:
    st.info("No attendance data found.")

conn.close()
