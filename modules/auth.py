import streamlit as st
from database import SessionLocal
from models import User

def login_page():
    st.title("Login")
    st.caption("v1.2 (Updated)") # Version Check
    
    with st.form("login_form"):
        # Username removed as per request
        password = st.text_input("Enter Access Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            db = SessionLocal()
            # Default to checking against the main Admin user "Ankur"
            user = db.query(User).filter(User.username == "Ankur").first()
            db.close()

            valid = False
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            if user and user.password_hash:
                try:
                    valid = pwd_context.verify(password, user.password_hash)
                except:
                   valid = False
            
            if valid:
                st.session_state["user_role"] = user.role
                st.session_state["username"] = user.username # Keep username in session for logic
                st.success(f"Welcome back, {user.username}!")
                st.rerun()
            else:
                st.error("Invalid Password.")

def logout():
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.rerun()
