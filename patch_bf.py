from database import SessionLocal
from sqlalchemy import text

def add_bf_column():
    db = SessionLocal()
    try:
        # Check if column exists
        result = db.execute(text("PRAGMA table_info(paper_rates)")).fetchall()
        columns = [row[1] for row in result]
        
        if "bf" not in columns:
            print("Adding 'bf' column to paper_rates table...")
            db.execute(text("ALTER TABLE paper_rates ADD COLUMN bf FLOAT DEFAULT 18.0"))
            db.commit()
            print("Column added successfully.")
        else:
            print("'bf' column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_bf_column()
