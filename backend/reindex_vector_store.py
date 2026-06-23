import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from database import Database
from vector_store import VectorStore
from config import Config

def reindex():
    print("=" * 60)
    print("REINDEXING VECTOR STORE FROM DATABASE")
    print("=" * 60)
    
    db_path = Config.DATABASE_PATH
    print(f"Database path: {db_path}")
    print(f"ChromaDB path: {Config.CHROMA_PATH}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file does not exist at {db_path}")
        return False
        
    db = Database(db_path)
    
    # Clean ChromaDB directory first to avoid schema mismatch and locking issues
    chroma_path = Config.CHROMA_PATH
    if os.path.exists(chroma_path):
        print(f"Cleaning ChromaDB directory at {chroma_path} before initializing client...")
        try:
            import shutil
            shutil.rmtree(chroma_path)
            print("SUCCESS: Cleaned ChromaDB directory")
        except Exception as e:
            print(f"WARNING: Could not clean ChromaDB directory: {e}")
            
    # Initialize Vector Store
    vector_store = VectorStore()
    
    # Reset Vector Store (deletes and recreates the collection to wipe out the old schema)
    print("Deleting old 'productivity_items' collection if exists...")
    try:
        vector_store.client.delete_collection("productivity_items")
        print("SUCCESS: Deleted old collection")
    except Exception as e:
        print(f"No existing collection to delete or error: {e}")
        
    # Recreate the collection
    vector_store.collection = vector_store.client.get_or_create_collection(
        name="productivity_items",
        metadata={"hnsw:space": "cosine"}
    )
    print("SUCCESS: Created new 'productivity_items' collection")
    
    # Fetch all items
    items = db.get_all_items()
    print(f"Found {len(items)} items in SQLite database to index.")
    
    indexed_count = 0
    for item in items:
        item_id = item['id']
        title = item.get('title', '') or ''
        description = item.get('description', '') or ''
        tags = item.get('tags', '') or ''
        
        search_text = f"{title} {description} {tags}".strip()
        if not search_text:
            search_text = "untitled"
            
        metadata = {
            'type': item.get('type', 'task'),
            'priority': item.get('priority', 'medium'),
            'tags': tags,
            'completed': bool(item.get('completed', 0))
        }
        
        vector_store.add_item(item_id, search_text, metadata)
        indexed_count += 1
        print(f"Indexed Item [{item_id}] - '{title}' (Completed: {metadata['completed']})")
        
    print("=" * 60)
    print(f"SUCCESS: Reindexed {indexed_count} items into ChromaDB.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    reindex()
