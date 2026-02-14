
import os
import sqlite3
import glob

def get_db_stats():
    db_path = "box_costing.db"
    if not os.path.exists(db_path):
        return "Database not found."
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        # Count Users
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['users'] = cursor.fetchone()[0]
        
        # Count Parties
        cursor.execute("SELECT COUNT(*) FROM parties")
        stats['parties'] = cursor.fetchone()[0]
        
        # Count Quotations
        cursor.execute("SELECT COUNT(*) FROM quotations")
        stats['quotations'] = cursor.fetchone()[0]
        
        # Total Quotation Amount
        cursor.execute("SELECT SUM(total_amount) FROM quotations")
        stats['total_value'] = cursor.fetchone()[0] or 0.0
        
        # Status Breakdown
        cursor.execute("SELECT status, COUNT(*) FROM quotations GROUP BY status")
        stats['status_breakdown'] = dict(cursor.fetchall())
        
        # Items
        cursor.execute("SELECT COUNT(*) FROM quotation_items")
        stats['items'] = cursor.fetchone()[0]

        conn.close()
        return stats
    except Exception as e:
        return f"Error reading database: {e}"

def get_file_stats():
    py_files = glob.glob("*.py") + glob.glob("modules/*.py")
    css_files = glob.glob("*.css")
    pdf_files = glob.glob("PDF/*.pdf")
    
    total_py_lines = 0
    for f in py_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                total_py_lines += len(file.readlines())
        except:
            continue
            
    db_size = 0
    if os.path.exists("box_costing.db"):
        db_size = os.path.getsize("box_costing.db")
    
    return {
        'py_count': len(py_files),
        'py_lines': total_py_lines,
        'css_count': len(css_files),
        'pdf_count': len(pdf_files),
        'db_size': db_size
    }

def print_stats():
    print("="*40)
    print("      BOX COSTING PROJECT STATS")
    print("="*40)
    
    f_stats = get_file_stats()
    print(f"[FILES]")
    print(f"  Python Files:    {f_stats['py_count']} ({f_stats['py_lines']} lines)")
    print(f"  CSS Files:       {f_stats['css_count']}")
    print(f"  Generated PDFs:  {f_stats['pdf_count']}")
    print(f"  Database Size:   {f_stats['db_size']/1024:.1f} KB")
    print("-" * 40)
    
    db_stats = get_db_stats()
    if isinstance(db_stats, dict):
        print(f"[DATABASE]")
        print(f"  Total Users:     {db_stats['users']}")
        print(f"  Active Parties:  {db_stats['parties']}")
        print(f"  Total Quotes:    {db_stats['quotations']}")
        for status, count in db_stats.get('status_breakdown', {}).items():
            print(f"    - {status}: {count}")
        print(f"  Total Items:     {db_stats['items']}")
        print(f"  Total Value:     Rs. {db_stats['total_value']:.2f}")
    else:
        print(f"[DATABASE] {db_stats}")
        
    print("="*40)

if __name__ == "__main__":
    print_stats()
