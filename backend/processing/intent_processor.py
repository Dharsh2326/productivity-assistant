from ..database import Database
from ..vector_store import VectorStore
from typing import Dict, List

class IntentProcessor:
    def __init__(self, database: Database, vector_store: VectorStore):
        self.db = database
        self.vector_store = vector_store
    
    def process_items(self, items: List[Dict]) -> List[Dict]:
        """
        Process parsed items from LLM
        """
        created_items = []
        
        for item in items:
            try:
                # Create item in database
                item_id = self.db.create_item(item)
                
                # Add to vector store for semantic search
                try:
                    search_text = f"{item.get('title', '')} {item.get('description', '') or ''} {' '.join(item.get('tags', []) or [])}"
                    
                    metadata = {
                        'type': item.get('type', 'task'),
                        'priority': item.get('priority', 'medium'),
                        'tags': ','.join(item.get('tags', []) or [])
                    }
                    self.vector_store.add_item(item_id, search_text, metadata)
                except Exception as vec_error:
                    # If vector store fails, continue anyway (non-critical)
                    print(f"Warning: Failed to add item to vector store: {vec_error}")
                
                # Get created item
                created_item = self.db.get_item_by_id(item_id)
                if created_item:
                    created_items.append(created_item)
            except Exception as e:
                print(f"Error processing item: {e}")
                # Continue with next item
                continue
        
        return created_items