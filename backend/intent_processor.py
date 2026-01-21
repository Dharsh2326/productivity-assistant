from .database import Database
from .vector_store import VectorStore
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
            item_id = self.db.create_item(item)
            
            search_text = f"{item.get('title', '')} {item.get('description', '')} {' '.join(item.get('tags', []))}"
            
            metadata = {
                'type': item.get('type'),
                'priority': item.get('priority', 'medium'),
                'tags': ','.join(item.get('tags', []))
            }
            self.vector_store.add_item(item_id, search_text, metadata)
            
            created_item = self.db.get_item_by_id(item_id)
            created_items.append(created_item)
        
        return created_items