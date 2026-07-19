import json
import re
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from config import Config
from database import Database
from vector_store import VectorStore

class ActionProcessor:
    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL

    def _override_relative_date(self, message: str, date_str: Optional[str]) -> Optional[str]:
        """
        Deterministic safety net: if the user's message contains an explicit
        relative-date keyword (today/tomorrow/day after tomorrow), force the
        DATE portion to Python's own calendar math instead of trusting the LLM,
        which is unreliable at date arithmetic. The TIME portion the LLM
        extracted (or the 09:00:00 default) is preserved untouched.
        """
        if not date_str:
            return date_str

        msg = message.lower()
        now = datetime.now()

        if re.search(r'\bday after tomorrow\b', msg):
            target_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        elif re.search(r'\btomorrow\b', msg):
            target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif re.search(r'\btoday\b|\btonight\b', msg):
            target_date = now.strftime("%Y-%m-%d")
        else:
            return date_str  # no explicit relative keyword -> trust the LLM's date

        time_part = "09:00:00"
        if "T" in date_str:
            time_part = date_str.split("T", 1)[1]

        return f"{target_date}T{time_part}"

    def _clean_title(self, message: str, extracted_title: Optional[str]) -> str:
        """
        Deterministic fallback: strips common command/filler words from a title
        if the LLM's extraction still contains them (e.g. it dumped the raw
        message in as the title instead of a clean phrase).
        """
        title = (extracted_title or message).strip()
        filler_pattern = re.compile(
            r'^(please\s+)?(today\s+|tomorrow\s+|tonight\s+)?(add|create|make|new)\s+'
            r'(a\s+|an\s+)?(task|reminder|note)?\s*(for|to|that|:)?\s*',
            re.IGNORECASE
        )
        cleaned = filler_pattern.sub('', title).strip()
        return cleaned if cleaned else title

    def parse_intent_and_entities(self, message: str) -> Dict[str, Any]:
        """Use Ollama to classify intent and extract entities"""
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_tomorrow = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        
        system_prompt = f"""You are an AI NLU parser. Today is {now.strftime('%A')}, {today_date}.
Classify the user prompt into one of these intents:
- 'create_task': Create a new task (e.g. "Buy milk tomorrow", "Task: revise DBMS")
- 'create_reminder': Create a new reminder (e.g. "Remind me to call Mom Friday at 6pm")
- 'create_note': Create a new note (e.g. "Note: DBMS normalization has 1NF, 2NF")
- 'update_item': Update details of an existing item (e.g. "Move DBMS assignment to Monday", "Change groceries priority to high", "Rename exam prep to DBMS revision")
- 'complete_item': Complete an existing item (e.g. "Mark groceries complete", "Finish DBMS assignment")
- 'restore_item': Mark a completed item as incomplete (e.g. "Restore groceries", "Mark DBMS assignment as incomplete")
- 'delete_item': Delete an item (e.g. "Delete gym reminder", "Delete all completed tasks")
- 'search': Search for items (e.g. "Search for DBMS assignment")
- 'summarize': Get a summary of workload (e.g. "What should I do today?", "Show my workload")
- 'query': A general conversational question or retrieval query (e.g. "What is DBMS?", "Why is my task overdue?")

Time conversions (use 24-hour format):
1am=01:00, 2am=02:00, 3am=03:00, 4am=04:00, 5am=05:00, 6am=06:00, 7am=07:00, 8am=08:00, 9am=09:00, 10am=10:00, 11am=11:00, 12pm=12:00
1pm=13:00, 2pm=14:00, 3pm=15:00, 4pm=16:00, 5pm=17:00, 6pm=18:00, 7pm=19:00, 8pm=20:00, 9pm=21:00, 10pm=22:00, 11pm=23:00
"today" = {today_date}, "tonight" = {today_date}, "tomorrow" = {tomorrow_date}, "day after tomorrow" = {day_after_tomorrow}, "Friday" = Friday date, etc. Default time is 09:00:00 if not specified.
Dates must be formatted as YYYY-MM-DDTHH:MM:SS.
IMPORTANT: If the user says "today", the date MUST be exactly {today_date} — never increment it.

CRITICAL INSTRUCTIONS FOR TARGET IDENTIFICATION vs NEW VALUES:
For 'update_item', 'complete_item', 'restore_item', and 'delete_item' intents:
- You MUST separate identifying the target item from the new values/fields to update.
- Place the identifying title/substring of the target item strictly in 'target_title'.
- Place any new values (e.g., new title, new description, new priority, new tags, new datetime) strictly inside 'update_fields'.
- NEVER put the new title or other updated fields in 'target_title'.
- Explicitly support these renaming/title update patterns:
  - "change reminder title from X to Y" -> target_title: "X", update_fields: {{"title": "Y"}}
  - "rename X to Y" -> target_title: "X", update_fields: {{"title": "Y"}}
  - "change X to Y" -> target_title: "X", update_fields: {{"title": "Y"}}
  - "update title X -> Y" -> target_title: "X", update_fields: {{"title": "Y"}}
  - "change title of X to Y" -> target_title: "X", update_fields: {{"title": "Y"}}

TITLE EXTRACTION RULES:
- The 'title' must be a CLEAN, natural title — strip filler/command words like "add", "create", "task", "note", "reminder", "please", and any time phrases ("today", "tomorrow", "at 9pm", etc.).
- Capitalize naturally (Title Case for short phrases).
- Examples:
  "today add task evening maths tution" -> title: "Evening Maths Tuition"
  "create task Math Revision" -> title: "Math Revision"
  "remind me to call mom tomorrow at 5pm" -> title: "Call Mom"

Extract entities matching this JSON structure:
{{
  "intent": "intent_name",
  "entities": {{
    "title": "Title for new items",
    "description": "Description if specified",
    "datetime": "YYYY-MM-DDTHH:MM:SS or null",
    "priority": "low" | "medium" | "high" or null,
    "tags": ["tag1", "tag2"] or null,
    "target_title": "Title/substring of target item to update/complete/delete",
    "target_type": "task" | "reminder" | "note" or null,
    "update_fields": {{
      "title": "New title if renaming",
      "description": "New description if updating",
      "datetime": "New ISO datetime if rescheduling",
      "priority": "low" | "medium" | "high" or null,
      "tags": ["tag1", "tag2"] or null
    }}
  }}
}}

CRITICAL: Output ONLY valid JSON. No explanation, no markdown blocks. Keep it clean.
"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\nUser Input: \"{message}\"\n\nJSON output:",
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 250,
                        "num_ctx": 2048
                    }
                },
                timeout=60
            )
            if response.status_code == 200:
                result_text = response.json().get('response', '{}').strip()
                parsed = json.loads(result_text)

                entities = parsed.get("entities", {}) or {}

                # Deterministic safety net: correct the date for explicit relative keywords
                if entities.get("datetime"):
                    entities["datetime"] = self._override_relative_date(message, entities["datetime"])

                update_fields = entities.get("update_fields")
                if isinstance(update_fields, dict) and update_fields.get("datetime"):
                    update_fields["datetime"] = self._override_relative_date(message, update_fields["datetime"])
                    entities["update_fields"] = update_fields

                parsed["entities"] = entities
                return parsed
            else:
                return {"intent": "query", "entities": {}}
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return {"intent": "query", "entities": {}}

    def _title_waterfall(self, items: List[Dict[str, Any]], target_title_stripped: str, target_lower: str):
        """Runs exact -> case-insensitive -> substring matching against a given item pool."""
        exact_matches = [item for item in items if item.get('title', '') == target_title_stripped]
        if exact_matches:
            return exact_matches, "exact_title", 1.0

        ci_matches = [item for item in items if item.get('title', '').lower() == target_lower]
        if ci_matches:
            return ci_matches, "case_insensitive_title", 1.0

        sub_matches = [item for item in items if target_lower in item.get('title', '').lower()]
        if sub_matches:
            return sub_matches, "substring_title", 1.0

        return None

    def find_matching_items(self, target_title: str, target_type: Optional[str] = None, completed: Optional[bool] = None) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Find matching items from SQLite by exact title, case-insensitive title, substring title,
        or semantic search fallback.
        target_type is treated as a SOFT preference: the LLM's type guess is often wrong when the
        user doesn't explicitly say "task"/"note"/"reminder", so we never let an incorrect type
        guess silently veto a real title match. `completed` is a HARD filter since it comes from
        the intent itself (complete_item/restore_item), not from an LLM guess.
        Returns: (matches, match_type, confidence_score)
        """
        if not target_title:
            return [], "none", 0.0
            
        all_items = self.db.get_all_items()

        # completed status is reliable (derived from intent, not guessed) - filter hard on it
        completed_filtered = [
            item for item in all_items
            if completed is None or bool(item.get('completed')) == completed
        ]

        target_title_stripped = target_title.strip()
        target_lower = target_title_stripped.lower()

        # Pass 1: honor the type guess (fast path when the LLM's guess happens to be correct)
        if target_type:
            type_and_completed_filtered = [
                item for item in completed_filtered if item.get('type') == target_type
            ]
            result = self._title_waterfall(type_and_completed_filtered, target_title_stripped, target_lower)
            if result:
                return result

        # Pass 2: retry without the type guess - a real title match should never be vetoed
        # by an incorrect type guess.
        result = self._title_waterfall(completed_filtered, target_title_stripped, target_lower)
        if result:
            return result

        filtered_items = completed_filtered

        # 4. Semantic search fallback (never use semantic search alone - this is only a fallback)
        try:
            where_filter = {}
            conditions = []
            if target_type:
                conditions.append({"type": target_type})
            if completed is not None:
                conditions.append({"completed": completed})
                
            if len(conditions) == 1:
                where_filter = conditions[0]
            elif len(conditions) > 1:
                where_filter = {"$and": conditions}
                
            semantic_results = self.vector_store.search(target_title, n_results=3, where=where_filter)
            semantic_matches = []
            best_score = 0.0
            for res in semantic_results:
                distance = res.get('distance', 1.0)
                similarity = 1.0 - distance
                item = self.db.get_item_by_id(res['id'])
                if item:
                    item['relevance_score'] = similarity
                    semantic_matches.append(item)
                    if similarity > best_score:
                        best_score = similarity
            if semantic_matches:
                return semantic_matches, "semantic_search", best_score
        except Exception as e:
            print(f"Warning: Semantic search in item matching failed: {e}")
            
        return [], "none", 0.0

    def validate_and_log_action(self, item: Dict[str, Any], action: str, new_values: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Log the matched item, action, and new values, and validate them before writing."""
        print("=== BEFORE EXECUTION LOG ===")
        print(f"Matched Item: {item}")
        print(f"Action: {action}")
        print(f"New Values: {new_values}")
        print("============================")
        
        # Validation checks
        if not item or 'id' not in item:
            return False, "Invalid matched item: missing ID"
            
        valid_actions = ("update_item", "complete_item", "restore_item", "delete_item")
        if action not in valid_actions:
            return False, f"Invalid action: {action}"
            
        # Specific validation on fields
        if action == "update_item":
            if not new_values:
                return False, "No update values provided"
            if 'title' in new_values:
                title_val = new_values['title']
                if title_val is not None and (not isinstance(title_val, str) or not title_val.strip()):
                    return False, "New title must be a non-empty string"
            if 'priority' in new_values:
                priority_val = new_values['priority']
                if priority_val not in (None, 'low', 'medium', 'high'):
                    return False, "Priority must be low, medium, or high"
            if 'completed' in new_values:
                if not isinstance(new_values['completed'], bool):
                    return False, "Completed status must be a boolean"
                    
        return True, None

    def execute_create(self, item_type: str, title: str, description: Optional[str], dt: Optional[str], priority: str, tags: list) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Execute create action with transaction safety and verification"""
        item_data = {
            'type': item_type,
            'title': (title or '').strip(),
            'description': description,
            'datetime': dt,
            'priority': priority if priority in ('low', 'medium', 'high') else 'medium',
            'tags': tags or [],
            'completed': False,
            'source': 'manual'
        }
        
        item_id = None
        try:
            # 1. SQLite create
            item_id = self.db.create_item(item_data)
            
            # Verify SQLite insert succeeded and ID returned
            if not item_id:
                raise Exception("SQLite insert did not return a valid item ID.")
            
            created_item = self.db.get_item_by_id(item_id)
            if not created_item:
                raise Exception("SQLite insert succeeded but item could not be retrieved.")
            
            # 2. ChromaDB sync
            search_text = f"{title} {description or ''} {' '.join(tags or [])}"
            metadata = {
                'type': item_type,
                'priority': priority if priority in ('low', 'medium', 'high') else 'medium',
                'tags': ','.join(tags or []) if isinstance(tags, list) else (tags or ''),
                'completed': False
            }
            
            # Try syncing with ChromaDB
            self.vector_store.add_item(item_id, search_text, metadata)
            
            # Verify ChromaDB sync succeeded
            synced_item = self.vector_store.get_item(item_id)
            if not synced_item:
                raise Exception("Verification failed: Vector store sync did not persist the new item.")

            # Log audit success
            print("=== ACTION AUDIT ===")
            print(f"Intent: create_{item_type}")
            print(f"Target ID: {item_id}")
            print(f"Target Title: {title}")
            print("Operation: Create")
            print("SQLite: SUCCESS")
            print("Vector Store: SUCCESS")
            print("UI Refresh: EMITTED")
            print("====================")
            
            return True, created_item, None
            
        except Exception as e:
            # Rollback SQLite if ChromaDB sync failed
            if item_id is not None:
                try:
                    self.db.delete_item(item_id)
                except Exception as db_err:
                    print(f"Critical error: SQLite rollback failed during create failure: {db_err}")
            
            print("=== ACTION FAILURE ===")
            print(f"Intent: create_{item_type}")
            print(f"Reason: ChromaDB sync or SQLite verification failed. Details: {str(e)}")
            print("======================")
            
            error_msg = f"Sync failed. SQLite database changes rolled back. Details: {str(e)}"
            return False, {}, error_msg

    def execute_update(self, item_id: int, updates: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Execute update action with transaction safety and persistence verification"""
        # Safety net: never let a stray leading/trailing space slip into a stored title.
        # A visually-invisible space here silently breaks exact/case-insensitive matching
        # on every future reference to this item.
        if 'title' in updates and isinstance(updates['title'], str):
            updates['title'] = updates['title'].strip()

        original_item = self.db.get_item_by_id(item_id)
        if not original_item:
            print("=== ACTION FAILURE ===")
            print("Intent: update_item")
            print(f"Reason: Item with ID {item_id} not found in database.")
            print("======================")
            return False, {}, "Item not found in database."
            
        # Validate and log before writing
        valid, err = self.validate_and_log_action(original_item, "update_item", updates)
        if not valid:
            print("=== ACTION FAILURE ===")
            print("Intent: update_item")
            print(f"Reason: Validation failed: {err}")
            print("======================")
            return False, {}, f"Validation failed: {err}"
            
        try:
            # 1. SQLite update
            success = self.db.update_item(item_id, updates)
            if not success:
                raise Exception("SQLite update failed to modify any rows.")
                
            # Fetch updated state and verify persistence
            updated_item = self.db.get_item_by_id(item_id)
            if not updated_item:
                raise Exception("Updated item could not be retrieved.")
            
            for key, val in updates.items():
                if key == 'tags' and isinstance(val, list):
                    val = ','.join(val)
                if updated_item.get(key) != val:
                    raise Exception(f"Persistence verification failed: {key} expected {val}, got {updated_item.get(key)}")
            
            # 2. ChromaDB sync
            title = updated_item.get('title', '') or ''
            description = updated_item.get('description', '') or ''
            tags = updated_item.get('tags', '') or ''
            search_text = f"{title} {description} {tags}".strip()
            metadata = {
                'type': updated_item.get('type', 'task'),
                'priority': updated_item.get('priority', 'medium'),
                'tags': tags,
                'completed': bool(updated_item.get('completed', False))
            }
            self.vector_store.add_item(item_id, search_text, metadata)
            
            # Verify ChromaDB sync succeeded
            synced_item = self.vector_store.get_item(item_id)
            if not synced_item:
                raise Exception("Verification failed: Vector store sync did not persist the update.")
            
            # Audit log success
            op = "Complete" if updates.get("completed") is True else "Restore" if updates.get("completed") is False else "Update"
            if "title" in updates:
                op = "Rename"
            print("=== ACTION AUDIT ===")
            print("Intent: update_item")
            print(f"Target ID: {item_id}")
            print(f"Target Title: {original_item.get('title')}")
            print(f"Operation: {op}")
            if "title" in updates:
                print(f"New Title: {updates['title']}")
            print("SQLite: SUCCESS")
            print("Vector Store: SUCCESS")
            print("UI Refresh: EMITTED")
            print("====================")
            
            return True, updated_item, None
            
        except Exception as e:
            # Rollback SQLite update
            try:
                revert_data = {
                    'title': original_item.get('title'),
                    'description': original_item.get('description'),
                    'datetime': original_item.get('datetime'),
                    'priority': original_item.get('priority'),
                    'tags': original_item.get('tags'),
                    'completed': original_item.get('completed')
                }
                self.db.update_item(item_id, revert_data)
            except Exception as db_err:
                print(f"Critical error: SQLite rollback failed during update failure: {db_err}")
                
            print("=== ACTION FAILURE ===")
            print("Intent: update_item")
            print(f"Reason: ChromaDB sync or verification failed. Details: {str(e)}")
            print("======================")
            
            error_msg = f"Sync failed. SQLite database changes rolled back. Details: {str(e)}"
            return False, {}, error_msg

    def execute_delete(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """Execute delete action with transaction safety and verification"""
        original_item = self.db.get_item_by_id(item_id)
        if not original_item:
            print("=== ACTION FAILURE ===")
            print("Intent: delete_item")
            print(f"Reason: Item with ID {item_id} not found in database.")
            print("======================")
            return False, "Item not found in database."
            
        # Validate and log before writing
        valid, err = self.validate_and_log_action(original_item, "delete_item", {})
        if not valid:
            print("=== ACTION FAILURE ===")
            print("Intent: delete_item")
            print(f"Reason: Validation failed: {err}")
            print("======================")
            return False, f"Validation failed: {err}"
            
        try:
            # 1. SQLite delete first
            success = self.db.delete_item(item_id)
            if not success:
                raise Exception("SQLite deletion failed to affect any rows.")
                
            # Verify deleted from SQLite
            deleted_check = self.db.get_item_by_id(item_id)
            if deleted_check:
                raise Exception("Verification failed: item still exists in SQLite.")
            
            # 2. ChromaDB sync delete
            try:
                self.vector_store.delete_item(item_id)
                # Verify ChromaDB deletion succeeded
                if self.vector_store.get_item(item_id) is not None:
                    raise Exception("Vector store sync failed: item still exists in ChromaDB.")
            except Exception as e:
                # Rollback SQLite delete if ChromaDB sync failed by inserting original item back
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO items (
                        id, type, title, description, datetime, priority, tags, 
                        completed, source, external_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    original_item['id'],
                    original_item['type'],
                    original_item['title'],
                    original_item['description'],
                    original_item['datetime'],
                    original_item['priority'],
                    original_item['tags'],
                    original_item['completed'],
                    original_item['source'],
                    original_item['external_id'],
                    original_item['created_at'],
                    original_item['updated_at']
                ))
                conn.commit()
                conn.close()
                raise Exception(f"ChromaDB sync delete failed, SQLite deletion rolled back. Details: {str(e)}")
            
            # Audit log success
            print("=== ACTION AUDIT ===")
            print("Intent: delete_item")
            print(f"Target ID: {item_id}")
            print(f"Target Title: {original_item.get('title')}")
            print("Operation: Delete")
            print("SQLite: SUCCESS")
            print("Vector Store: SUCCESS")
            print("UI Refresh: EMITTED")
            print("====================")
            
            return True, None
            
        except Exception as e:
            print("=== ACTION FAILURE ===")
            print("Intent: delete_item")
            print(f"Reason: {str(e)}")
            print("======================")
            return False, str(e)