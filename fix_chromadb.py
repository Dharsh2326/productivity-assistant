import os
import shutil
import sqlite3
import time
import stat

CHROMA_PATH = 'data/chroma'

def handle_remove_readonly(func, path, exc):
    """Handle readonly files on Windows"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def fix_chromadb():
    """Fix ChromaDB database by deleting corrupted files"""
    chroma_path = CHROMA_PATH
    sqlite_file = os.path.join(chroma_path, 'chroma.sqlite3')
    
    if not os.path.exists(chroma_path):
        print(f"✅ ChromaDB directory doesn't exist at {chroma_path}")
        print("   It will be created automatically on next backend start.")
        return
    
    print(f"🔧 Fixing ChromaDB database at {chroma_path}...")
    print()
    
    # Try to close any open SQLite connections
    if os.path.exists(sqlite_file):
        try:
            conn = sqlite3.connect(sqlite_file)
            conn.close()
            time.sleep(0.2)
            print("✅ Closed SQLite connection")
        except Exception as e:
            print(f"⚠️  Could not close SQLite connection: {e}")
    
    # Delete the SQLite file
    if os.path.exists(sqlite_file):
        try:
            os.remove(sqlite_file)
            print(f"✅ Deleted ChromaDB SQLite file: chroma.sqlite3")
        except PermissionError:
            print(f"⚠️  SQLite file is locked. Trying to rename it...")
            try:
                backup_name = sqlite_file + '.old.' + str(int(time.time()))
                os.rename(sqlite_file, backup_name)
                print(f"✅ Renamed SQLite file to: {os.path.basename(backup_name)}")
            except Exception as e:
                print(f"❌ Could not rename file: {e}")
                print(f"   Please close any programs using this file and try again.")
                print(f"   Or manually delete: {os.path.abspath(sqlite_file)}")
                return
        except Exception as e:
            print(f"❌ Error deleting SQLite file: {e}")
    
    # Delete subdirectories
    if os.path.exists(chroma_path):
        deleted_count = 0
        for item in os.listdir(chroma_path):
            item_path = os.path.join(chroma_path, item)
            if os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path, onerror=handle_remove_readonly)
                    print(f"✅ Deleted subdirectory: {item}")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️  Could not delete subdirectory {item}: {e}")
        
        if deleted_count > 0:
            print(f"✅ Deleted {deleted_count} subdirectories")
    
    # Check if directory is now empty or only has backup files
    remaining = [f for f in os.listdir(chroma_path) if not f.endswith('.old.')]
    if not remaining:
        print()
        print("✅ ChromaDB database has been reset successfully!")
        print("   It will be recreated automatically on next backend start.")
    else:
        print()
        print(f"⚠️  Some files remain in the directory: {remaining}")
        print("   You may need to manually delete them or restart your computer.")

if __name__ == '__main__':
    print("=" * 60)
    print("ChromaDB Database Fix Tool")
    print("=" * 60)
    print()
    fix_chromadb()
    print()
    print("=" * 60)

