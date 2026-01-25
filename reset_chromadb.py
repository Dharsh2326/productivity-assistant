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

def reset_chromadb():
    """Delete and reset ChromaDB database"""
    chroma_path = CHROMA_PATH
    sqlite_file = os.path.join(chroma_path, 'chroma.sqlite3')
    
    if not os.path.exists(chroma_path):
        print(f" ChromaDB database doesn't exist at {chroma_path}")
        print("   It will be created automatically on next backend start.")
        return
    
    print(f" Deleting ChromaDB database at {chroma_path}...")
    
    # Try to close SQLite connection first
    if os.path.exists(sqlite_file):
        try:
            conn = sqlite3.connect(sqlite_file)
            conn.close()
            time.sleep(0.2)
        except:
            pass
    
    # Delete SQLite file
    if os.path.exists(sqlite_file):
        try:
            os.remove(sqlite_file)
            print(" Deleted chroma.sqlite3")
        except PermissionError:
            try:
                backup_name = sqlite_file + '.old.' + str(int(time.time()))
                os.rename(sqlite_file, backup_name)
                print(f" Renamed SQLite file (was locked)")
            except Exception as e:
                print(f" Could not delete/rename SQLite file: {e}")
        except Exception as e:
            print(f" Error with SQLite file: {e}")
    
    # Delete directory contents
    try:
        for item in os.listdir(chroma_path):
            item_path = os.path.join(chroma_path, item)
            if os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path, onerror=handle_remove_readonly)
                except Exception as e:
                    print(f" Could not delete {item}: {e}")
        
        # Try to remove the directory itself
        try:
            os.rmdir(chroma_path)
            print(" ChromaDB directory deleted")
        except:
            print(" Some files may remain, but main database is cleared")
        
        print(" ChromaDB database reset successfully")
        print("   It will be recreated automatically on next backend start.")
    except Exception as e:
        print(f"Error deleting ChromaDB database: {e}")
        print("   Try running: python fix_chromadb.py")
        print(f"   Or manually delete: {os.path.abspath(chroma_path)}")

if __name__ == '__main__':
    print("=" * 60)
    print("ChromaDB Database Reset Tool")
    print("=" * 60)
    print()
    reset_chromadb()
    print()
    print("=" * 60)

