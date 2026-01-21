import chromadb
from chromadb.config import Settings
from .config import Config
from typing import List, Dict

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="productivity_items",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_item(self, item_id: int, text: str, metadata: Dict):
        """Add an item to the vector store"""
        self.collection.add(
            ids=[str(item_id)],
            documents=[text],
            metadatas=[metadata]
        )
    
    def search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Semantic search for items"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['ids'] or not results['ids'][0]:
            return []
        
        items = []
        for i in range(len(results['ids'][0])):
            items.append({
                'id': int(results['ids'][0][i]),
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return items
    
    def delete_item(self, item_id: int):
        """Delete an item from vector store"""
        try:
            self.collection.delete(ids=[str(item_id)])
        except:
            pass