import streamlit as st
from database import init_db, SessionLocal
from models import User
# from modules.masters import masters_page
# from modules.calculator import calculator_page # To be implemented
# from modules.reports import reports_page # To be implemented

st.set_page_config(page_title="Honest Packaging Costing", layout="wide", page_icon="📦")

from modules.auth import login_page, logout

import os
import time
import logging
from database import init_db, SessionLocal
from models import User
from modules.backup_utils import auto_backup_check

from modules.utils import get_resource_path

# 0. App Version & Logging
VERSION = "1.2.0"
logging.basicConfig(filename="error.log", level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Initialize Database
init_db()
auto_backup_check()

# Load Custom CSS
def local_css(file_name):
    full_path = get_resource_path(file_name)
    if os.path.exists(full_path):
        with open(full_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# Check Login
if "user_role" not in st.session_state or st.session_state["user_role"] is None:
    login_page()
    st.stop()

# Sidebar
# Sidebar Header
import os
sidebar_logo = get_resource_path("sidebar_header.png")
if os.path.exists(sidebar_logo):
    st.sidebar.image(sidebar_logo, use_container_width=True)
else:
    st.sidebar.title(f"📦 Honest Packaging")
# st.sidebar.caption(f"Logged in as: {st.session_state['username']} ({st.session_state['user_role']})")

st.sidebar.title("Navigation")
st.sidebar.caption(f"v{VERSION} | Honest Packaging")

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

        # --- DATABASE BACKUP SECTION ---
        st.divider()
        st.subheader("💾 Database Backup & Restore")
        from modules.backup_utils import create_backup, list_backups, restore_backup, delete_backup, get_backup_dir
        from models import Settings
        
        db = SessionLocal()
        
        # 1. Path Configuration
        current_path = get_backup_dir()
        with st.expander("⚙️ Configure Backup Path", expanded=False):
            new_path = st.text_input("Local Storage Path", value=current_path, help="e.g. D:/Backups/BoxCosting")
            if st.button("Save Path"):
                # Update settings table
                s = db.query(Settings).filter(Settings.key == "backup_path").first()
                if not s:
                    s = Settings(key="backup_path", value=new_path)
                    db.add(s)
                else:
                    s.value = new_path
                db.commit()
                st.success(f"Path updated to: {new_path}")
                st.rerun()
                
            if st.button("Reset to Default (backups/)"):
                s = db.query(Settings).filter(Settings.key == "backup_path").first()
                if s:
                    s.value = "backups"
                    db.commit()
                st.rerun()

        st.caption(f"Current Path: `{os.path.abspath(current_path)}`")
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🔹 Backup Now", use_container_width=True):
            success, path = create_backup()
            if success:
                st.success(f"Backup created: {os.path.basename(path)}")
            else:
                st.error(f"Backup failed: {path}")
        
        backups = list_backups()
        if backups:
            st.markdown("### Available Backups")
            for b in backups:
                b_cols = st.columns([3, 1, 1])
                b_cols[0].write(f"📄 {b}")
                
                # Restore Logic
                with b_cols[1]:
                    if st.button("🔄 Restore", key=f"res_{b}"):
                        st.session_state[f"confirm_restore_{b}"] = True
                
                # Delete Logic
                if b_cols[2].button("🗑️", key=f"del_b_{b}"):
                    delete_backup(b)
                    st.rerun()
                
                # Confirmation Popup for Restore
                if st.session_state.get(f"confirm_restore_{b}", False):
                    st.warning(f"CRITICAL: This will overwrite ALL current data with backup '{b}'. Are you sure?")
                    c1, c2 = st.columns(2)
                    if c1.button("YES, Restore", key=f"yes_res_{b}"):
                        success, msg = restore_backup(b)
                        if success:
                            st.success(msg)
                            st.session_state[f"confirm_restore_{b}"] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                    if c2.button("Cancel", key=f"no_res_{b}"):
                        st.session_state[f"confirm_restore_{b}"] = False
                        st.rerun()
        else:
            st.info("No backups found.")

    st.divider()
    
    # --- EMAIL CONFIGURATION SECTION ---
    if st.session_state.get("user_role") == "Admin":
        st.divider()
        st.subheader("📧 Email SMTP Configuration")
        
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        
        # Load current values
        current_smtp = {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "",
            "password": ""
        }
        
        if os.path.exists(secrets_path):
            try:
                import tomllib # Python 3.11+
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    if "smtp" in data:
                        current_smtp.update(data["smtp"])
            except:
                # Fallback for older python or parsing error
                pass

        with st.expander("📝 Edit SMTP Settings", expanded=False):
            with st.form("smtp_form"):
                srv = st.text_input("SMTP Server", value=current_smtp["server"])
                prt = st.number_input("Port", value=int(current_smtp["port"]), step=1)
                usr = st.text_input("Email / Username", value=current_smtp["username"])
                pwd = st.text_input("App Password", value=current_smtp["password"], type="password")
                
                if st.form_submit_button("Update Configuration"):
                    os.makedirs(".streamlit", exist_ok=True)
                    with open(secrets_path, "w") as f:
                        f.write("[smtp]\n")
                        f.write(f'server = "{srv}"\n')
                        f.write(f"port = {prt}\n")
                        f.write(f'username = "{usr}"\n')
                        f.write(f'password = "{pwd}"\n')
                    st.success("Secrets updated! Please restart the application for changes to take effect.")
                    st.rerun()

    st.divider()

