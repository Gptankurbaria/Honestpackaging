import sqlite3
import os

DB_FILE = "box_costing.db"

def add_email_column():
    if not os.path.exists(DB_FILE):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE parties ADD COLUMN email TEXT")
        conn.commit()
        print("Successfully added 'email' column to 'parties' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("Column 'email' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_email_column()
