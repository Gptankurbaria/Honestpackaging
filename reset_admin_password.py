from passlib.context import CryptContext
from database import SessionLocal
from models import User
import sys

# Consistently using pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def reset_password(new_password="admin"):
    db = SessionLocal()
    try:
        # Default user checked in auth.py is "Ankur"
        user = db.query(User).filter(User.username == "Ankur").first()
        if not user:
            print("User 'Ankur' not found. Creating new Admin user.")
            user = User(username="Ankur", role="Admin")
            db.add(user)
        
        hashed_pw = pwd_context.hash(new_password)
        user.password_hash = hashed_pw
        db.commit()
        print(f"Success! Admin (Ankur) password has been reset to: '{new_password}'")
        
    except Exception as e:
        print(f"Error resetting password: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        new_pwd = sys.argv[1]
    else:
        new_pwd = "admin"
    
    print(f"Resetting Admin password...")
    reset_password(new_pwd)
