import streamlit as st
from database import init_db
# from modules.masters import masters_page
# from modules.calculator import calculator_page # To be implemented
# from modules.reports import reports_page # To be implemented

st.set_page_config(page_title="Honest Packaging Costing", layout="wide", page_icon="📦")

from modules.auth import login_page, logout

# Initialize Database
init_db()

# Load Custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# Check Login
if "user_role" not in st.session_state or st.session_state["user_role"] is None:
    login_page()
    st.stop()

# Sidebar
# Sidebar Header
import os
if os.path.exists("sidebar_header.png"):
    st.sidebar.image("sidebar_header.png", use_container_width=True)
else:
    st.sidebar.title(f"📦 Honest Packaging")
# st.sidebar.caption(f"Logged in as: {st.session_state['username']} ({st.session_state['user_role']})")

st.sidebar.title("Navigation")

# Define menu based on role
# Define menu based on role
# 1. New Quotation 2. Report 3. Masters 4. User Details
menus = [
    "1. New Quotation", 
    "2. Report", 
    "3. Masters", 
    "4. User Details"
]

selected_menu = st.sidebar.radio("Go to", menus)

if selected_menu == "1. New Quotation":
    from modules.calculator import calculator_page
    calculator_page()

elif selected_menu == "2. Report":
    from modules.reports import reports_page
    reports_page()

elif selected_menu == "3. Masters":
    from modules.masters import masters_page
    masters_page()

elif selected_menu == "4. User Details":
    from modules.masters import party_master_page # Fallback or implementation
    # User Details logic
    st.title("User Details")
    st.write(f"**Current User:** {st.session_state.get('username', 'Unknown')}")
    st.write(f"**Role:** {st.session_state.get('user_role', 'Unknown')}")
    st.divider()
    st.info("User profile management is coming soon.")

