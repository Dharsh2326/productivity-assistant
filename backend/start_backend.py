import os
import sys
import sqlite3
import shutil
from pathlib import Path

from backend import app

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

def print_header(text):
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60)

def check_ollama():
    """Check if Ollama is running"""
    import requests
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            print(" Ollama is running")
            models = response.json().get('models', [])
            if models:
                print(f"   Available models: {', '.join([m['name'] for m in models])}")
            return True
        else:
            print("  Ollama is running but returned unexpected status")
            return False
    except:
        if os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT"):
            print(" Ollama not available in cloud — AI features disabled")
            return True
        print(" Ollama is NOT running")
        print("   Please start Ollama first: ollama serve")
        print("   Or install from: https://ollama.ai")
        return False

def check_database():
    """Check and initialize database"""
    from config import Config
    
    db_path = Config.DATABASE_PATH
    db_exists = os.path.exists(db_path)
    
    if not db_exists:
        print(f" Creating new database at: {db_path}")
    else:
        print(f" Database exists at: {db_path}")
        
        # Check if it has the correct schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(items)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            required_cols = ['id', 'type', 'title', 'description', 'datetime', 
                           'priority', 'tags', 'completed', 'source', 'external_id',
                           'created_at', 'updated_at']
            
            missing = [col for col in required_cols if col not in columns]
            
            if missing:
                print(f"  Database missing columns: {', '.join(missing)}")
                print("   Backing up and recreating database...")
                conn.close()
                
                # Backup old database
                backup_path = db_path + '.backup'
                shutil.copy(db_path, backup_path)
                print(f"   Backed up to: {backup_path}")
                
                # Delete old database
                os.remove(db_path)
                print("   Old database removed")
                return False
            else:
                cursor.execute("SELECT COUNT(*) FROM items")
                count = cursor.fetchone()[0]
                print(f"   Contains {count} items")
                print(f"   Schema: {len(columns)} columns ✓")
                conn.close()
                return True
        except Exception as e:
            print(f" Database error: {e}")
            conn.close()
            return False
    
    # Initialize database using Database class
    from database import Database
    db = Database(Config.DATABASE_PATH)
    print("Database initialized successfully")
    return True

def check_mock_data():
    """Check if mock data files exist"""
    from config import Config
    
    if not Config.USE_MOCK_DATA:
        print("Mock data mode is disabled")
        return True
    
    base_dir = Path(__file__).resolve().parent
    mock_dir = base_dir / 'ingestion' / 'mock_data'
    
    calendar_file = mock_dir / 'calendar_events.json'
    email_file = mock_dir / 'email_messages.json'
    
    if calendar_file.exists() and email_file.exists():
        print(f"Mock data files found in: {mock_dir}")
        return True
    else:
        print(f"Mock data files missing in: {mock_dir}")
        if not calendar_file.exists():
            print(f"   Missing: {calendar_file.name}")
        if not email_file.exists():
            print(f"   Missing: {email_file.name}")
        return False

def check_static_directory():
    """Ensure static directory exists"""
    from config import Config
    
    static_dir = Path(__file__).resolve().parent / 'static' / 'visualizations'
    static_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Static directory ready: {static_dir}")
    
    # List existing visualizations
    images = list(static_dir.glob('*.png'))
    if images:
        print(f"   Contains {len(images)} existing visualization(s)")
    
    return True

def reset_chromadb():
    """Reset ChromaDB if needed"""
    from config import Config
    
    chroma_path = Path(Config.CHROMA_PATH)
    
    if chroma_path.exists():
        print(f"ChromaDB directory exists: {chroma_path}")
        
        # Check if it has any issues
        sqlite_file = chroma_path / 'chroma.sqlite3'
        if sqlite_file.exists():
            print(f"   ChromaDB SQLite file found")
        return True
    else:
        print(f" ChromaDB will be initialized at: {chroma_path}")
        return True

def main():
    print_header("PRODUCTIVITY ASSISTANT - BACKEND STARTUP")
    
    print("\n Running Pre-flight Checks...\n")
    
    checks = {
        "Configuration": lambda: __import__('config').Config.validate(),
        "Ollama Service": check_ollama,
        "Database": check_database,
        "Mock Data Files": check_mock_data,
        "Static Directory": check_static_directory,
        "ChromaDB": reset_chromadb
    }
    
    results = {}
    for name, check_func in checks.items():
        print(f"\n Checking: {name}")
        print("-" * 60)
        try:
            results[name] = check_func()
        except Exception as e:
            print(f" Error during {name} check: {e}")
            results[name] = False
    
    print_header("PRE-FLIGHT CHECK RESULTS")
    
    all_passed = True
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status.ljust(10)} - {name}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print("\n Some checks failed. Please fix the issues above before starting.\n")
        return False
    
    print_header("ALL CHECKS PASSED - STARTING SERVER")
    
    # Print configuration
    from config import Config
    Config.print_config()
    
    # Start Flask app
    print("Starting Flask application on http://localhost:5000\n")
    
    from app import app
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)