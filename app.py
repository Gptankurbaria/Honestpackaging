import streamlit as st
from database import init_db, SessionLocal
from models import User
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
    # from modules.masters import party_master_page # Removed invalid import
    # User Details logic
    st.title("User Details")
    st.write(f"**Current User:** {st.session_state.get('username', 'Unknown')}")
    st.write(f"**Role:** {st.session_state.get('user_role', 'Unknown')}")
    st.divider()
    st.divider()
    
    # User Management Section
    if st.session_state.get("user_role") == "Admin":
        st.divider()
        st.subheader("👤 User Management")
        
        db = SessionLocal()
        users = db.query(User).all()
        
        # Add New User
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["Admin", "Accountant", "Sales"])
                if st.form_submit_button("Create User"):
                    if new_user and new_pass:
                        from passlib.context import CryptContext
                        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
                        hashed_pw = pwd_context.hash(new_pass)
                        
                        user_exists = db.query(User).filter(User.username == new_user).first()
                        if user_exists:
                            st.error(f"User '{new_user}' already exists.")
                        else:
                            u = User(username=new_user, password_hash=hashed_pw, role=new_role)
                            db.add(u)
                            db.commit()
                            st.success(f"User '{new_user}' created!")
                            st.rerun()
                    else:
                        st.error("Username and Password are required.")

        # List Users
        st.markdown("---")
        u_cols = st.columns([2, 2, 1])
        u_cols[0].markdown("**Username**")
        u_cols[1].markdown("**Role**")
        u_cols[2].markdown("**Action**")
        
        for u in users:
            row = st.columns([2, 2, 1])
            row[0].write(u.username)
            row[1].write(u.role)
            # Prevent deleting yourself
            if u.username != st.session_state.get("username"):
                if row[2].button("🗑️", key=f"del_u_{u.id}", help=f"Delete {u.username}"):
                    db.delete(u)
                    db.commit()
                    st.toast(f"User {u.username} deleted.")
                    st.rerun()
            else:
                row[2].caption("(Current)")
        
        db.close()

    st.divider()
    
    st.subheader("📧 Email Configuration Setup")
    st.markdown("""
    To enable email functionality, you need to configure your SMTP settings in the secrets file.
    
    **1. Locate/Create Secrets File:**
    - **Local:** `.streamlit/secrets.toml` inside your project folder.
    - **Cloud:** App Dashboard -> Settings -> Secrets.
    
    **2. Configuration Format:**
    Copy and paste the following into the file:
    ```toml
    [smtp]
    server = "smtp.gmail.com"
    port = 587
    username = "your_email@gmail.com"
    password = "your_app_password"
    ```
    
    > **Note:** For Gmail, use an **App Password** (enabled in Google Account > Security), NOT your login password.
    """)

