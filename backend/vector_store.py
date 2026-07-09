import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import logging
logging.getLogger('chromadb').setLevel(logging.CRITICAL)

import chromadb
from chromadb.config import Settings
from config import Config  # Changed from .config
from typing import List, Dict
import shutil
import time
import sqlite3

class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client. Runs a pre-flight schema check first so we
        can delete a stale chroma.sqlite3 BEFORE ChromaDB opens and locks it."""
        os.environ['ANONYMIZED_TELEMETRY'] = 'False'

        # --- PRE-FLIGHT: inspect existing SQLite schema without opening ChromaDB ---
        chroma_path = Config.CHROMA_PATH
        sqlite_file = os.path.join(chroma_path, 'chroma.sqlite3')

        if os.path.exists(sqlite_file):
            schema_ok = self._check_schema(sqlite_file)
            if not schema_ok:
                print("WARNING: ChromaDB schema mismatch detected on pre-flight check. Resetting now...")
                self._reset_chromadb()
                time.sleep(0.5)

        # --- NORMAL INIT ---
        try:
            self.client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
            self.collection = self.client.get_or_create_collection(
                name="productivity_items",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            # Release any file locks from client reference before reset
            self.client = None
            self.collection = None
            import gc
            gc.collect()
            time.sleep(0.5)

            error_msg = str(e).lower()
            if "no such column" in error_msg or "operationalerror" in error_msg:
                # Schema is still bad (e.g. reset didn't fully clean) — try once more
                print("WARNING: ChromaDB still broken after pre-flight reset. Forcing full wipe...")
                self._reset_chromadb(force=True)
                time.sleep(1.0)
                self.client = chromadb.PersistentClient(
                    path=chroma_path,
                    settings=Settings(anonymized_telemetry=False, allow_reset=True)
                )
                self.collection = self.client.get_or_create_collection(
                    name="productivity_items",
                    metadata={"hnsw:space": "cosine"}
                )
                print("SUCCESS: ChromaDB database reset and reinitialized successfully")
            else:
                raise e

    def _check_schema(self, sqlite_file: str) -> bool:
        """Open the chroma.sqlite3 directly (read-only) and check if the
        collections table has the expected columns. Returns True if OK."""
        try:
            conn = sqlite3.connect(f"file:{sqlite_file}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(collections)")
            cols = {row[1] for row in cursor.fetchall()}
            conn.close()
            # ChromaDB 0.4.x / 0.5.x requires 'topic' column; older files lack it
            if not cols:
                return True  # empty/fresh db is fine
            required = {'id', 'name', 'dimension', 'topic'}
            return required.issubset(cols)
        except Exception:
            # If we can't read it at all, treat as stale and reset
            return False

    def _reset_chromadb(self, force: bool = False):
        """Delete the ChromaDB data directory contents reliably on Windows.
        Uses a retry loop with increasing delays, and falls back to
        Windows cmd 'del /F' for files that Python can't unlock."""
        import subprocess
        import stat

        chroma_path = Config.CHROMA_PATH
        sqlite_file = os.path.join(chroma_path, 'chroma.sqlite3')

        # Close any dangling sqlite3 connections from this process
        try:
            if os.path.exists(sqlite_file):
                conn = sqlite3.connect(sqlite_file)
                conn.close()
        except Exception:
            pass

        # Retry loop — Windows releases locks within ~500 ms after process exit
        for attempt in range(5):
            if not os.path.exists(sqlite_file):
                break
            try:
                os.chmod(sqlite_file, stat.S_IWRITE)
                os.remove(sqlite_file)
                print("SUCCESS: Deleted ChromaDB SQLite file")
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                # Final fallback: Windows cmd force-delete (bypasses Python handle restrictions)
                try:
                    result = subprocess.run(
                        ['cmd', '/C', f'del /F /Q "{sqlite_file}"'],
                        capture_output=True, timeout=5
                    )
                    if not os.path.exists(sqlite_file):
                        print("SUCCESS: Force-deleted ChromaDB SQLite file via cmd")
                    else:
                        print(f"WARNING: Could not delete {sqlite_file} even with cmd del")
                except Exception as e2:
                    print(f"WARNING: cmd del fallback failed: {e2}")
            except Exception as e:
                print(f"WARNING: Error deleting SQLite file: {e}")
                break

        # Remove all subdirectories (segment files)
        if os.path.exists(chroma_path):
            try:
                for item in os.listdir(chroma_path):
                    item_path = os.path.join(chroma_path, item)
                    if os.path.isdir(item_path):
                        try:
                            shutil.rmtree(item_path, onerror=self._handle_remove_readonly)
                            print(f"SUCCESS: Deleted ChromaDB subdirectory: {item}")
                        except Exception as e:
                            print(f"WARNING: Could not delete subdirectory {item}: {e}")
            except Exception as e:
                print(f"WARNING: Error cleaning ChromaDB directory: {e}")

    
    def _handle_remove_readonly(self, func, path, exc):
        """Handle readonly files on Windows"""
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    def add_item(self, item_id: int, text: str, metadata: Dict):
        """Add or update an item in the vector store"""
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
                elif isinstance(value, bool):
                    clean_metadata[key] = value
                elif isinstance(value, (int, float)):
                    clean_metadata[key] = value
                elif isinstance(value, (list, dict)):
                    clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            self.collection.upsert(
                ids=[str(item_id)],
                documents=[text],
                metadatas=[clean_metadata]
            )
        except Exception as e:
            print(f"Warning: Failed to add/update item in vector store: {e}")
    
    def search(self, query: str, n_results: int = 10, where: Dict = None) -> List[Dict]:
        """Semantic search for items"""
        if not self.collection:
            return []
        try:
            query_params = {
                "query_texts": [query],
                "n_results": n_results
            }
            if where:
                query_params["where"] = where

            results = self.collection.query(**query_params)

            if not results.get('ids') or not results['ids'][0]:
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
        except Exception as e:
            print(f"Warning: Vector search failed: {e}")
            return []

    def get_item(self, item_id: int) -> Dict:
        """Get an item directly by ID to verify synchronization"""
        if not self.collection:
            return None
        try:
            res = self.collection.get(ids=[str(item_id)])
            if res and res.get('ids') and len(res['ids']) > 0:
                return {
                    'id': res['ids'][0],
                    'document': res['documents'][0] if res.get('documents') else None,
                    'metadata': res['metadatas'][0] if res.get('metadatas') else None
                }
        except Exception:
            pass
        return None
    
    def delete_item(self, item_id: int):
        """Delete an item from vector store"""
        try:
            self.collection.delete(ids=[str(item_id)])
        except:
            pass