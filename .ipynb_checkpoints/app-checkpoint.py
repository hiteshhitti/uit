# app.py
import streamlit as st
from db import create_tables
from utils.helpers import apply_auto_fines, check_and_update_leave_status

create_tables()
apply_auto_fines()

check_and_update_leave_status()

st.set_page_config(page_title="Student Management System", layout="wide")


st.title("🎓 Student Management System")
st.write("Welcome to the dashboard. Use the sidebar to navigate to different modules.")
