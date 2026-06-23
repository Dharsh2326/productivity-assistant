import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import Database
from vector_store import VectorStore
from config import Config

def run_test_query(vector_store, db, query, exclude_completed=True):
    print(f"\nSearch Query: '{query}' (exclude_completed={exclude_completed})")
    print("-" * 60)
    
    # 1. Setup metadata filter
    where_filter = {}
    if exclude_completed:
        where_filter["completed"] = False
        
    # 2. Query Vector Store
    results = vector_store.search(query, n_results=10, where=where_filter)
    
    # 3. Print matches and filter by similarity threshold
    passed_count = 0
    for result in results:
        item_id = result['id']
        distance = result.get('distance')
        similarity = 1.0 - distance if distance is not None else 0.0
        
        item = db.get_item_by_id(item_id)
        title = item.get('title', 'Unknown') if item else 'Unknown'
        completed = item.get('completed', 0) if item else 0
        
        status_str = "Completed" if completed else "Active"
        
        # Check threshold
        passed = similarity >= Config.SEARCH_SIMILARITY_THRESHOLD
        pass_marker = "PASS" if passed else "FILTERED"
        
        print(f"[{pass_marker}] Item ID: {item_id:2d} | Title: {title:30s} | Status: {status_str:9s} | Similarity: {similarity:.4f}")
        if passed:
            passed_count += 1
            
    print(f"Total results passing threshold (>= {Config.SEARCH_SIMILARITY_THRESHOLD}): {passed_count}")
    print("-" * 60)

def main():
    print("=" * 60)
    print("AuraPlan Semantic Search Quality Verification")
    print("=" * 60)
    print(f"Similarity Threshold: {Config.SEARCH_SIMILARITY_THRESHOLD}")
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"ChromaDB: {Config.CHROMA_PATH}")
    print("=" * 60)
    
    db = Database(Config.DATABASE_PATH)
    vector_store = VectorStore()
    
    # Run the tests requested by the user
    # Test 1: Search for "groceries" (expecting groceries items, completed excluded by default)
    run_test_query(vector_store, db, "groceries", exclude_completed=True)
    
    # Test 2: Search for "exam" (expecting "exam" item. Note: ID 21 "exam" is completed.
    # Exclude completed by default -> should be empty.
    # Exclude completed = False -> should retrieve ID 21)
    run_test_query(vector_store, db, "exam", exclude_completed=True)
    run_test_query(vector_store, db, "exam", exclude_completed=False)
    
    # Test 3: Search for "DBMS" (expecting DBMS normalization note)
    run_test_query(vector_store, db, "DBMS", exclude_completed=True)

if __name__ == "__main__":
    main()
