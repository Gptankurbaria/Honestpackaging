from database import SessionLocal, Base, engine
from models import ReelSize

def create_reel_table():
    print("Creating reel_sizes table...")
    ReelSize.__table__.create(bind=engine, checkfirst=True)
    print("Table created successfully.")
    
    # Add some defaults if empty
    db = SessionLocal()
    if db.query(ReelSize).count() == 0:
        defaults = [40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60]
        for w in defaults:
            db.add(ReelSize(width=float(w), unit="Inch"))
        db.commit()
        print("Added default reel sizes (40-60 inch).")
    db.close()

if __name__ == "__main__":
    create_reel_table()
