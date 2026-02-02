import sqlite3

def fix_db():
    print("Fixing database...")
    try:
        conn = sqlite3.connect("box_costing.db")
        cursor = conn.cursor()
        
        # Check if column exists to avoid error
        cursor.execute("PRAGMA table_info(quotation_items)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "layer_details" not in columns:
            print("Adding 'layer_details' column...")
            # JSON type text is fine for SQLite
            cursor.execute("ALTER TABLE quotation_items ADD COLUMN layer_details JSON")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'layer_details' already exists. No action needed.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_db()
