"""
Database schema checker and validator
Checks if database exists and has correct schema
"""
import sqlite3
import os
from .config import Config

def check_schema():
    """Check if database schema is correct"""
    db_path = Config.DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("✅ Database will be created automatically on first run")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if items table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='items'
        """)
        
        if not cursor.fetchone():
            print("❌ 'items' table not found")
            conn.close()
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(items)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        required_columns = [
            'id', 'type', 'title', 'description', 'datetime', 
            'priority', 'tags', 'completed', 'created_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {', '.join(missing_columns)}")
            conn.close()
            return False
        
        print("✅ Database schema is correct")
        print(f"✅ Found {len(columns)} columns in 'items' table")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        print(f"✅ Database contains {count} items")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Checking database schema...\n")
    check_schema()

