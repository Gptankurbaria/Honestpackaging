from passlib.context import CryptContext
from database import SessionLocal
from models import User
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_password(new_password="admin"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "Admin").first()
        if not user:
            print("User 'Admin' not found. Creating new Admin user.")
            user = User(username="Admin", role="Admin")
            db.add(user)
        
        hashed_pw = pwd_context.hash(new_password)
        user.password_hash = hashed_pw
        db.commit()
        print(f"Success! Admin password has been reset to: '{new_password}'")
        
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
