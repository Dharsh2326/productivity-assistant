import chromadb
from chromadb.config import Settings
from config import Config  # Changed from .config
from typing import List, Dict
import os
import shutil
import time
import sqlite3

class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with error handling for schema issues"""
        try:
            # Disable telemetry to avoid warnings
            import os
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            
            self.client = chromadb.PersistentClient(
                path=Config.CHROMA_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.collection = self.client.get_or_create_collection(
                name="productivity_items",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "no such column" in error_msg or "operationalerror" in error_msg:
                print(f"⚠️  ChromaDB schema mismatch detected. Resetting ChromaDB database...")
                self._reset_chromadb()
                time.sleep(0.5)
                self.client = chromadb.PersistentClient(
                    path=Config.CHROMA_PATH,
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name="productivity_items",
                    metadata={"hnsw:space": "cosine"}
                )
                print("✅ ChromaDB database reset and reinitialized successfully")
            else:
                raise e
    
    def _reset_chromadb(self):
        """Reset ChromaDB database by deleting SQLite file and directory"""
        chroma_path = Config.CHROMA_PATH
        sqlite_file = os.path.join(chroma_path, 'chroma.sqlite3')
        
        try:
            if os.path.exists(sqlite_file):
                conn = sqlite3.connect(sqlite_file)
                conn.close()
                time.sleep(0.2)
        except:
            pass
        
        if os.path.exists(sqlite_file):
            try:
                os.remove(sqlite_file)
                print(f"✅ Deleted ChromaDB SQLite file")
            except PermissionError:
                try:
                    backup_name = sqlite_file + '.old.' + str(int(time.time()))
                    os.rename(sqlite_file, backup_name)
                    print(f"✅ Renamed old SQLite file to {os.path.basename(backup_name)}")
                except Exception as e2:
                    print(f"⚠️  Could not rename file: {e2}")
            except Exception as e:
                print(f"⚠️  Error deleting SQLite file: {e}")
        
        if os.path.exists(chroma_path):
            try:
                for item in os.listdir(chroma_path):
                    item_path = os.path.join(chroma_path, item)
                    if os.path.isdir(item_path):
                        try:
                            shutil.rmtree(item_path, onerror=self._handle_remove_readonly)
                            print(f"✅ Deleted ChromaDB subdirectory: {item}")
                        except Exception as e:
                            print(f"⚠️  Could not delete subdirectory {item}: {e}")
            except Exception as e:
                print(f"⚠️  Error cleaning ChromaDB directory: {e}")
    
    def _handle_remove_readonly(self, func, path, exc):
        """Handle readonly files on Windows"""
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    def add_item(self, item_id: int, text: str, metadata: Dict):
        """Add an item to the vector store"""
        try:
            if not self.collection:
                print("Warning: Vector store collection not initialized, skipping vector add")
                return
            
            if not text or not text.strip():
                text = "untitled"
            
            clean_metadata = {}
            for key, value in metadata.items():
                if value is None:
                    clean_metadata[key] = ""
                elif isinstance(value, (list, dict)):
                    clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            self.collection.add(
                ids=[str(item_id)],
                documents=[text],
                metadatas=[clean_metadata]
            )
        except Exception as e:
            print(f"Warning: Failed to add item to vector store: {e}")
    
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