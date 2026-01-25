import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a timestamped backup of the database"""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    shutil.copy(db_path, backup_path)
    print(f" Backup created: {backup_path}")
    return backup_path

def check_schema(db_path):
    """Check current database schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(items)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    conn.close()
    return columns

def migrate_database(db_path):
    """Add missing columns to database"""
    
    print("\n" + "="*60)
    print("DATABASE MIGRATION TOOL")
    print("="*60)
    
    if not os.path.exists(db_path):
        print(f"\nDatabase not found: {db_path}")
        print("   Database will be created automatically when you start the backend.")
        return False
    
    # Backup first
    print("\n Creating backup...")
    backup_path = backup_database(db_path)
    if not backup_path:
        return False
    
    # Check current schema
    print("\n Checking current schema...")
    columns = check_schema(db_path)
    print(f"   Found {len(columns)} columns: {', '.join(columns.keys())}")
    
    # Determine what needs to be added
    missing_columns = []
    if 'source' not in columns:
        missing_columns.append(('source', 'TEXT DEFAULT "manual"'))
    if 'external_id' not in columns:
        missing_columns.append(('external_id', 'TEXT'))
    
    if not missing_columns:
        print("\n Database schema is already up to date!")
        print("   No migration needed.")
        return True
    
    print(f"\n Missing columns detected: {', '.join([col[0] for col in missing_columns])}")
    print("   Starting migration...")
    
    # Perform migration
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        for col_name, col_def in missing_columns:
            print(f"\n   Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE items ADD COLUMN {col_name} {col_def}")
            print(f"    Added {col_name}")
        
        # Update existing rows to have 'manual' source if NULL
        if 'source' in [col[0] for col in missing_columns]:
            cursor.execute("UPDATE items SET source = 'manual' WHERE source IS NULL")
            print("    Set default values for existing items")
        
        # Create index for external_id
        if 'external_id' in [col[0] for col in missing_columns]:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_external_id ON items(external_id)")
            print("    Created index on external_id")
        
        # Create index for datetime if not exists
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_datetime ON items(datetime)")
        print("    Created index on datetime")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(items)")
        final_columns = cursor.fetchall()
        
        print("\n Migration completed successfully!")
        print(f"\n Final schema ({len(final_columns)} columns):")
        for col in final_columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Get item count
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        print(f"\n Database contains {count} items")
         
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n Migration failed: {e}")
        print("   Rolling back...")
        conn.rollback()
        conn.close()
        
        print(f"\n Restoring from backup...")
        if os.path.exists(backup_path):
            shutil.copy(backup_path, db_path)
            print("    Backup restored")
        
        return False

def recreate_database(db_path):
    """Completely recreate the database (WARNING: LOSES ALL DATA)"""
    
    print("\n" + "="*60)
    print("  RECREATE DATABASE (DESTRUCTIVE)")
    print("="*60)
    print("\nWARNING: This will DELETE all existing data!")
    
    confirm = input("\nType 'YES' to confirm: ")
    if confirm != 'YES':
        print(" Operation cancelled")
        return False
    
    if os.path.exists(db_path):
        backup_database(db_path)
        os.remove(db_path)
        print(f" Deleted old database: {db_path}")
    
    # Delete ChromaDB too
    chroma_path = os.path.join(os.path.dirname(db_path), 'chroma')
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        print(f" Deleted ChromaDB: {chroma_path}")
    
    print("\n Database will be recreated on next backend startup")
    print("   All data has been lost (backup was created)")
    
    return True

if __name__ == '__main__':
    # Get database path from config
    import sys
    from pathlib import Path
    
    # Add backend to path
    backend_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(backend_dir))
    
    from config import Config
    
    print("\nDatabase location:", Config.DATABASE_PATH)
    print("\nChoose an option:")
    print("1. Migrate existing database (keeps data, adds missing columns)")
    print("2. Recreate database (DELETES all data)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        success = migrate_database(Config.DATABASE_PATH)
        sys.exit(0 if success else 1)
    elif choice == '2':
        success = recreate_database(Config.DATABASE_PATH)
        sys.exit(0 if success else 1)
    else:
        print("Exiting...")
        sys.exit(0)