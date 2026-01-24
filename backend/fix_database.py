import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = 'backend/data/productivity.db'
BACKUP_PATH = 'backend/data/productivity_backup.db'

def backup_database():
    """Backup existing database"""
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, BACKUP_PATH)
        print(f"✅ Backed up database to {BACKUP_PATH}")
        return True
    return False

def migrate_database():
    """Migrate database to new schema"""
    
    if not os.path.exists(DB_PATH):
        print("❌ No database found. Backend will create it on first run.")
        return
    
    # Backup first
    backup_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get current columns
        cursor.execute("PRAGMA table_info(items)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        print("\n📋 Current columns:", list(columns.keys()))
        
        # Add missing columns
        if 'source' not in columns:
            print("\n➕ Adding 'source' column...")
            cursor.execute("ALTER TABLE items ADD COLUMN source TEXT DEFAULT 'manual'")
            cursor.execute("UPDATE items SET source = 'manual' WHERE source IS NULL")
            print("✅ Added 'source' column")
        
        if 'external_id' not in columns:
            print("\n➕ Adding 'external_id' column...")
            cursor.execute("ALTER TABLE items ADD COLUMN external_id TEXT")
            print("✅ Added 'external_id' column")
        
        # Create index if not exists
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_external_id ON items(external_id)")
        print("✅ Created index on external_id")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(items)")
        final_columns = cursor.fetchall()
        
        print("\n✅ Migration complete! Final schema:")
        for col in final_columns:
            print(f"   - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        conn.rollback()
        print("\n🔄 Restoring backup...")
        conn.close()
        if os.path.exists(BACKUP_PATH):
            shutil.copy(BACKUP_PATH, DB_PATH)
            print("✅ Backup restored")
    
    finally:
        conn.close()

def recreate_database():
    """Delete and recreate database with new schema"""
    
    if os.path.exists(DB_PATH):
        # Backup first
        backup_database()
        
        print("\n🗑️  Deleting old database...")
        os.remove(DB_PATH)
        print("✅ Old database deleted")
    
    # Delete ChromaDB data too
    chroma_path = 'backend/data/chroma'
    if os.path.exists(chroma_path):
        print("\n🗑️  Deleting ChromaDB data...")
        shutil.rmtree(chroma_path)
        print("✅ ChromaDB data deleted")
    
    print("\n✨ Database will be recreated on next backend start with new schema")

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE SCHEMA FIX UTILITY")
    print("=" * 60)
    
    choice = input("\nChoose an option:\n1. Migrate existing database (keep data)\n2. Recreate database (lose data)\n\nEnter 1 or 2: ")
    
    if choice == '1':
        migrate_database()
    elif choice == '2':
        recreate_database()
    else:
        print("Invalid choice. Exiting.")