import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
import logging
logging.getLogger('chromadb').setLevel(logging.CRITICAL)
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from vector_store import VectorStore
from processing.ask_aura_service import AskAuraService
from config import Config

def run_tests():
    print("=== Ask Aura Verification Script ===")
    
    # 1. Initialize services
    db = Database(Config.DATABASE_PATH)
    vector_store = VectorStore()
    ask_aura_service = AskAuraService(db, vector_store)
    
    # Check if empty database first
    all_items = db.get_all_items()
    print(f"Current workspace has {len(all_items)} items.")
    
    # 2. Test Queries
    queries = [
        "What do I need to do today?",
        "What is overdue?",
        "Show my notes.",
        "Show my reminders.",
        "DBMS exam related questions"
    ]
    
    for query in queries:
        print(f"\n--- Testing Query: '{query}' ---")
        try:
            result = ask_aura_service.get_assistant_response(query, history=[])
            
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                # Truncate response output for clean logs
                response = result.get('response', '')
                truncated = response[:120] + "..." if len(response) > 120 else response
                print(f"Response: {truncated}")
                print(f"Sources consulted ({len(result.get('sources', []))} items):")
                for src in result.get('sources', [])[:3]:
                    print(f"  - [{src['type'].upper()}] (ID: {src['id']}) Title: {src['title']} | Score: {src.get('relevance_score')}")
                if len(result.get('sources', [])) > 3:
                    print(f"  ... and {len(result.get('sources', [])) - 3} more sources.")
            else:
                print(f"Error: {result.get('error')}")
        except Exception as e:
            print(f"Exception during test: {e}")

if __name__ == '__main__':
    run_tests()
