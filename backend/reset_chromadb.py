import os
import shutil
from config import Config  # Changed from .config

def reset_chromadb():
    """Delete and reset ChromaDB database"""
    chroma_path = Config.CHROMA_PATH
    
    if not os.path.exists(chroma_path):
        print(f" ChromaDB database doesn't exist at {chroma_path}")
        print("   It will be created automatically on next backend start.")
        return
    
    print(f" Deleting ChromaDB database at {chroma_path}...")
    try:
        shutil.rmtree(chroma_path)
        print(" ChromaDB database deleted successfully")
        print("   It will be recreated automatically on next backend start.")
    except Exception as e:
        print(f"Error deleting ChromaDB database: {e}")
        print("   You may need to manually delete the directory:")
        print(f"   {os.path.abspath(chroma_path)}")

if __name__ == '__main__':
    print("=" * 60)
    print("ChromaDB Database Reset Tool")
    print("=" * 60)
    print()
    reset_chromadb()
    print()
    print("=" * 60)