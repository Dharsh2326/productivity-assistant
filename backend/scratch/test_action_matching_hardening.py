import os
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from vector_store import VectorStore
from processing.ask_aura_service import AskAuraService
from config import Config

def run_tests():
    print("=== Hardened Action Matching Verification ===")
    db = Database(Config.DATABASE_PATH)
    vector_store = VectorStore()
    ask_aura_service = AskAuraService(db, vector_store)

    # Let's check how the system parses title renaming
    queries = [
        "change reminder title from as result to result day",
        "rename yoga class to advanced yoga",
        "change DBMS normalization has 1NF, 2NF to DBMS Normalization",
        "delete yoga class",
        "complete Sleep",
    ]

    for query in queries:
        print(f"\n--- Parsing User Query: '{query}' ---")
        parsed = ask_aura_service.action_processor.parse_intent_and_entities(query)
        intent = parsed.get("intent")
        entities = parsed.get("entities", {})
        print(f"Intent: {intent}")
        print(f"Entities: {entities}")

        target_title = entities.get("target_title")
        target_type = entities.get("target_type")
        completed_filter = None
        if intent == "complete_item":
            completed_filter = False
        elif intent == "restore_item":
            completed_filter = True
            
        matches, mtype, conf = ask_aura_service.action_processor.find_matching_items(
            target_title=target_title,
            target_type=target_type,
            completed=completed_filter
        )
        print(f"Matches found: {len(matches)} | Type: {mtype} | Conf: {conf}")

        print(f"--- Simulating get_assistant_response for: '{query}' ---")
        res = ask_aura_service.get_assistant_response(query, history=[])
        print(f"Response success: {res.get('success')}")
        print(f"Action performed: {res.get('action_performed')}")
        print(f"Requires disambiguation: {res.get('requires_disambiguation')}")
        print(f"Pending confirmation: {res.get('pending_confirmation')}")
        print(f"Response: {res.get('response')}")

if __name__ == '__main__':
    run_tests()
