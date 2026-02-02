from passlib.context import CryptContext
from database import SessionLocal
from models import User
import sys
import argparse

# Switched to pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_user(username, password, role):
    db = SessionLocal()
    try:
        # Check if exists
        user = db.query(User).filter(User.username == username).first()
        if user:
            print(f"User '{username}' already exists. Updating password.")
        else:
            print(f"Creating new user '{username}' with role '{role}'.")
            user = User(username=username, role=role)
            db.add(user)
        
        hashed_pw = pwd_context.hash(password)
        user.password_hash = hashed_pw
        db.commit()
        print(f"Success! User '{username}' created/updated.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update a user.")
    parser.add_argument("username", type=str, help="Username")
    parser.add_argument("password", type=str, help="Password")
    parser.add_argument("--role", type=str, default="Sales", choices=["Admin", "Accountant", "Sales"], help="User Role")
    
    args = parser.parse_args()
    
    create_user(args.username, args.password, args.role)
