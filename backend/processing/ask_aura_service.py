import re
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import Config
from database import Database
from vector_store import VectorStore
from processing.action_processor import ActionProcessor
from processing.pending_confirmation_store import PendingConfirmationStore

class AskAuraService:
    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
        
        # New orchestration services
        self.action_processor = ActionProcessor(db, vector_store)
        self.confirmation_store = PendingConfirmationStore()
        self.disambiguation_store = PendingConfirmationStore()
        self.sessions_history: Dict[str, List[Dict[str, Any]]] = {}

    def _is_conversational_recall(self, message: str) -> bool:
        msg = message.lower().strip()
        keywords = [
            "what did we talk about", "what did we say", "what was my last",
            "show previous conversation", "show our conversation", "show the history",
            "what did i ask", "what did i say", "previous message", "talk about earlier"
        ]
        return any(kw in msg for kw in keywords)

    def _detect_bulk_intent(self, message: str) -> Optional[Dict[str, Any]]:
        msg = message.lower().strip()
        # "remainder(s)" is an extremely common typo for "reminder(s)" - normalize it
        # so bulk-pattern matching isn't brittle to this one specific misspelling.
        msg = re.sub(r'\bremainders\b', 'reminders', msg)
        msg = re.sub(r'\bremainder\b', 'reminder', msg)
        
        # Define the bulk patterns and their filters
        bulk_patterns = {
            "all completed reminders": {"type": "reminder", "completed": True, "overdue": False},
            "all completed tasks": {"type": "task", "completed": True, "overdue": False},
            "all reminders": {"type": "reminder", "completed": None, "overdue": False},
            "all overdue tasks": {"type": "task", "completed": False, "overdue": True},
            "all overdue reminders": {"type": "reminder", "completed": False, "overdue": True},
            "all completed items": {"type": None, "completed": True, "overdue": False},
            "all active tasks": {"type": "task", "completed": False, "overdue": False},
            "all active reminders": {"type": "reminder", "completed": False, "overdue": False},
            "all tasks": {"type": "task", "completed": None, "overdue": False},
            "all items": {"type": None, "completed": None, "overdue": False}
        }
        
        for pattern, filters in bulk_patterns.items():
            if pattern in msg:
                return filters
        return None

    def _get_bulk_items(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_items = self.db.get_all_items()
        matched = []
        today_str = datetime.now().date().isoformat()
        
        for item in all_items:
            # 1. Filter by type
            if filters.get("type") and item.get("type") != filters["type"]:
                continue
                
            # 2. Filter by completed
            if filters.get("completed") is not None:
                if bool(item.get("completed")) != filters["completed"]:
                    continue
                    
            # 3. Filter by overdue
            if filters.get("overdue"):
                item_date_str = item.get('datetime', '').split('T')[0] if item.get('datetime') else ''
                if bool(item.get("completed")) or not item_date_str or item_date_str >= today_str:
                    continue
                    
            matched.append(item)
        return matched

    def get_assistant_response(self, message: str, history: List[Dict[str, Any]], session_id: Optional[str] = "default_session", confirm_action: Optional[str] = None) -> Dict[str, Any]:
        """
        Process the user query with Phase 2 Action Pipeline:
        Detect action intent, resolve matching items with ambiguity detection,
        confirm dangerous operations, execute safely with transaction checks,
        or fall back to read-only RAG mode.
        """
        try:
            # 1. Verify session ID
            session_id = session_id or "default_session"
            if session_id not in self.sessions_history:
                self.sessions_history[session_id] = []

            # Maintain in-memory session history
            if message and confirm_action is None:
                self.sessions_history[session_id].append({"role": "user", "content": message})
                self.sessions_history[session_id] = self.sessions_history[session_id][-30:]

            # Check if this is a conversational recall question
            if message and self._is_conversational_recall(message) and len(self.sessions_history[session_id]) > 1:
                history_str = ""
                # Exclude the last message which is the current query itself
                for chat in self.sessions_history[session_id][:-1]:
                    role = "User" if chat.get("role") == "user" else "Aura"
                    history_str += f"{role}: {chat.get('content')}\n"
                    
                system_prompt = (
                    "You are Aura, the personal productivity assistant for AuraPlan.\n"
                    "The user is asking about your past conversation or previous messages.\n"
                    "Consult the provided session conversation history below and answer their question directly and concisely.\n"
                    "If the information is not in the history, say so politely."
                )
                
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"--- SESSION CONVERSATION HISTORY ---\n{history_str}\n"
                    f"User: {message}\n"
                    f"Aura:"
                )
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 400,
                            "num_ctx": 2048
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    reply = response.json().get('response', '').strip()
                    self.sessions_history[session_id].append({"role": "assistant", "content": reply})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return {
                        "success": True,
                        "response": reply,
                        "sources": [],
                        "action_performed": False
                    }

            # 1.5. Check if responding to Disambiguation
            pending_disambig = self.disambiguation_store.get_pending(session_id)
            if pending_disambig:
                # The user should have replied with an ID or title.
                msg_clean = message.lower().strip()
                selected_id = None
                
                # Check if msg_clean is just digits
                digit_match = re.search(r'\d+', msg_clean)
                if digit_match:
                    selected_id = int(digit_match.group(0))
                
                valid_ids = pending_disambig.get("target_ids", [])
                
                if selected_id in valid_ids:
                    # Clear disambiguation
                    self.disambiguation_store.clear_pending(session_id)
                    
                    # We found the ID, now we simulate the action execution or push it to confirmation
                    action_type = pending_disambig["action_type"]
                    payload = pending_disambig["payload"]
                    
                    # Instead of executing directly, if it requires confirmation (like delete), 
                    # we should probably just send it to confirmation or execute directly.
                    # Let's execute directly since they selected the exact one, UNLESS it's a bulk action (handled elsewhere)
                    res = self._execute_confirmed_action(action_type, [selected_id], payload)
                    if res.get("success") and res.get("response"):
                        self.sessions_history[session_id].append({"role": "assistant", "content": res["response"]})
                        self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return res
                elif msg_clean in ("cancel", "stop", "abort", "nevermind"):
                    self.disambiguation_store.clear_pending(session_id)
                    return {
                        "success": True,
                        "response": "Action cancelled.",
                        "action_performed": False
                    }
                else:
                    # Clear it if they say something unrelated
                    self.disambiguation_store.clear_pending(session_id)

            # 2. Check if responding to a Pending Confirmation
            pending = self.confirmation_store.get_pending(session_id)
            
            # Check for affirmative/negative keywords if not explicitly clicked via button
            msg_clean = message.lower().strip()
            is_confirm = confirm_action == "confirm" or msg_clean in ("yes", "confirm", "y", "ok", "sure", "approve", "do it")
            is_cancel = confirm_action == "cancel" or msg_clean in ("no", "cancel", "n", "don't do it", "stop", "abort")
            
            if pending:
                if is_confirm:
                    action_type = pending["action_type"]
                    target_ids = pending["target_ids"]
                    payload = pending["payload"]
                    
                    self.confirmation_store.clear_pending(session_id)
                    res = self._execute_confirmed_action(action_type, target_ids, payload)
                    if res.get("success") and res.get("response"):
                        self.sessions_history[session_id].append({"role": "assistant", "content": res["response"]})
                        self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return res
                elif is_cancel:
                    self.confirmation_store.clear_pending(session_id)
                    cancel_res = {
                        "success": True,
                        "response": "Action cancelled successfully.",
                        "action_performed": False,
                        "action_type": pending["action_type"],
                        "affected_items": [],
                        "pending_confirmation": None
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": cancel_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return cancel_res
                elif confirm_action is None and msg_clean not in ("", " "):
                    # User typed something else entirely; let's treat it as a new intent (breaking confirmation context)
                    self.confirmation_store.clear_pending(session_id)

            # Check if database is empty first
            all_db_items = self.db.get_all_items()
            parsed = None
            if not all_db_items:
                # Allow creations even if database is empty
                parsed = self.action_processor.parse_intent_and_entities(message)
                intent = parsed.get("intent", "query")
                if intent not in ("create_task", "create_reminder", "create_note"):
                    empty_res = {
                        "success": True,
                        "response": "Your AuraPlan workspace is currently empty! You can start by adding tasks, notes, or reminders using the input box above (e.g., 'Submit project report tomorrow at 5 PM' or 'Note: DBMS Normalization is important'). Once you add some items, I'll be able to help you manage, summarize, and prioritize your workload.",
                        "sources": [],
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": empty_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return empty_res

            # 3. Parse Intent & Entities (reuse the parse from the empty-check above if we already did it)
            if parsed is None:
                parsed = self.action_processor.parse_intent_and_entities(message)
            intent = parsed.get("intent", "query")
            entities = parsed.get("entities", {})

            # 4. Handle Action Intents
            if intent in ("create_task", "create_reminder", "create_note"):
                title = self.action_processor._clean_title(message, entities.get("title"))
                desc = entities.get("description")
                dt = entities.get("datetime")
                raw_priority = entities.get("priority")
                priority = raw_priority if raw_priority in ("low", "medium", "high") else "medium"
                tags = entities.get("tags") or []
                
                item_type = "task"
                if intent == "create_reminder":
                    item_type = "reminder"
                elif intent == "create_note":
                    item_type = "note"

                success, created_item, err = self.action_processor.execute_create(
                    item_type=item_type,
                    title=title,
                    description=desc,
                    dt=dt,
                    priority=priority,
                    tags=tags
                )
                
                if not success:
                    fail_res = {
                        "success": False,
                        "error": err,
                        "response": "Task creation failed.",
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": fail_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return fail_res
                    
                type_lbl = item_type.capitalize()
                success_res = {
                    "success": True,
                    "response": f"✓ {type_lbl} created successfully.",
                    "action_performed": True,
                    "action_type": f"create_{item_type}",
                    "affected_items": [created_item]
                }
                self.sessions_history[session_id].append({"role": "assistant", "content": success_res["response"]})
                self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                return success_res

            elif intent in ("update_item", "complete_item", "restore_item", "delete_item"):
                # BULK / COLLECTION RECOGNITION
                bulk_filter = self._detect_bulk_intent(message)
                if bulk_filter:
                    matches = self._get_bulk_items(bulk_filter)
                    if not matches:
                        no_bulk_res = {
                            "success": True,
                            "response": "No matching items found to perform the action.",
                            "action_performed": False
                        }
                        self.sessions_history[session_id].append({"role": "assistant", "content": no_bulk_res["response"]})
                        self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                        return no_bulk_res

                    target_ids = [item["id"] for item in matches]
                    self.confirmation_store.set_pending(session_id, intent, target_ids, entities)
                    
                    lbl = "completed reminders" if bulk_filter.get("type") == "reminder" and bulk_filter.get("completed") else \
                          "completed tasks" if bulk_filter.get("type") == "task" and bulk_filter.get("completed") else \
                          "reminders" if bulk_filter.get("type") == "reminder" else \
                          "overdue tasks" if bulk_filter.get("type") == "task" and bulk_filter.get("overdue") else \
                          "overdue reminders" if bulk_filter.get("type") == "reminder" and bulk_filter.get("overdue") else \
                          "completed items" if bulk_filter.get("completed") else "items"
                          
                    action_verb = "delete" if intent == "delete_item" else "complete" if intent == "complete_item" else "restore" if intent == "restore_item" else "update"
                    response_text = f"I found {len(matches)} {lbl}. Are you sure you want to {action_verb} them?"
                    
                    bulk_confirm_res = {
                        "success": True,
                        "response": response_text,
                        "action_performed": False,
                        "pending_confirmation": {
                            "action_type": intent,
                            "target_ids": target_ids,
                            "affected_items": matches
                        }
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": bulk_confirm_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return bulk_confirm_res

                # SINGLE ITEM RECOGNITION
                target_title = entities.get("target_title")
                target_type = entities.get("target_type")
                
                # If rename/title update, make sure target and new title are identified separately
                is_rename = False
                if intent == "update_item":
                    update_fields = entities.get("update_fields", {}) or {}
                    if "title" in update_fields:
                        is_rename = True
                
                if not target_title:
                    missing_res = {
                        "success": True,
                        "response": "I couldn't identify which item you want to update. Please specify the title of the item you want to modify.",
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": missing_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return missing_res
                    
                if is_rename:
                    new_title = entities.get("update_fields", {}).get("title")
                    if not new_title:
                        missing_rename_res = {
                            "success": True,
                            "response": "I couldn't identify the new title for the update. Please clarify what new title you want to set.",
                            "action_performed": False
                        }
                        self.sessions_history[session_id].append({"role": "assistant", "content": missing_rename_res["response"]})
                        self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                        return missing_rename_res
                
                # Filter complete/restore matching items by their active/completed state to narrow search
                completed_filter = None
                if intent == "complete_item":
                    completed_filter = False
                elif intent == "restore_item":
                    completed_filter = True
                    
                matches, match_type, confidence_score = self.action_processor.find_matching_items(
                    target_title=target_title,
                    target_type=target_type,
                    completed=completed_filter
                )

                # No items matched - return failure directly, do not fall back to RAG
                if not matches:
                    no_match_res = {
                        "success": False,
                        "response": f"No matching items found for '{target_title}' to perform the action.",
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": no_match_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return no_match_res

                # AMBIGUITY RESOLUTION / DISAMBIGUATION SAFETY
                # If multiple items match with similar substring/semantic score, and we didn't specify bulk complete/delete
                is_bulk = "all" in message.lower() or "every" in message.lower() or "bulk" in message.lower()
                
                if len(matches) > 1 and not is_bulk:
                    # Save pending disambiguation state
                    valid_ids = [item["id"] for item in matches]
                    self.disambiguation_store.set_pending(session_id, intent, valid_ids, entities)
                    
                    items_list = "\n".join([f"- [{item['type'].upper()}] '{item['title']}' (ID: {item['id']})" for item in matches])
                    disambig_res = {
                        "success": True,
                        "requires_disambiguation": True,
                        "ambiguous_matches": matches,
                        "matches": matches,
                        "response": f"I found multiple items matching '{target_title}'. Which one did you mean?\n\n{items_list}\n\nPlease select the intended item.",
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": disambig_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return disambig_res

                # MATCH TYPE RESTRICTIONS
                # Semantic search matches must NEVER execute directly.
                if match_type == "semantic_search" or confidence_score < Config.SEARCH_SIMILARITY_THRESHOLD:
                    # Save pending disambiguation state
                    valid_ids = [item["id"] for item in matches]
                    self.disambiguation_store.set_pending(session_id, intent, valid_ids, entities)
                    
                    semantic_disambig_res = {
                        "success": True,
                        "requires_disambiguation": True,
                        "ambiguous_matches": matches,
                        "matches": matches,
                        "response": "I found a possible match, but I'm not confident enough to modify it. Please select the intended item.",
                        "action_performed": False
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": semantic_disambig_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return semantic_disambig_res

                # Single matched item or confirmed bulk action
                target_ids = [item["id"] for item in matches]
                
                # Check if confirmation is required
                needs_confirm = (intent == "delete_item") or (len(matches) > 1)
                
                if needs_confirm:
                    # Save pending action
                    self.confirmation_store.set_pending(session_id, intent, target_ids, entities)
                    
                    lbl = "item" if len(matches) == 1 else "items"
                    names = ", ".join([f"'{m['title']}'" for m in matches])
                    action_verb = "delete" if intent == "delete_item" else "update" if intent == "update_item" else "complete" if intent == "complete_item" else "restore"
                    
                    confirm_res = {
                        "success": True,
                        "response": f"I found {len(matches)} {lbl}: {names}. Confirm {action_verb}?",
                        "action_performed": False,
                        "pending_confirmation": {
                            "action_type": intent,
                            "target_ids": target_ids,
                            "affected_items": matches
                        }
                    }
                    self.sessions_history[session_id].append({"role": "assistant", "content": confirm_res["response"]})
                    self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return confirm_res
                else:
                    # Single item, safe operation -> execute immediately
                    exec_res = self._execute_confirmed_action(intent, target_ids, entities)
                    if exec_res.get("success") and exec_res.get("response"):
                        self.sessions_history[session_id].append({"role": "assistant", "content": exec_res["response"]})
                        self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
                    return exec_res

            # 5. Fallback to read-only retrieval mode (only for query, summarize, search)
            rag_res = self._fallback_rag_response(message, history)
            if rag_res.get("success") and rag_res.get("response"):
                self.sessions_history[session_id].append({"role": "assistant", "content": rag_res["response"]})
                self.sessions_history[session_id] = self.sessions_history[session_id][-30:]
            return rag_res

        except Exception as e:
            print(f"Error in AskAuraService Phase 2: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"An error occurred while answering your question: {str(e)}",
                "sources": []
            }

    def _execute_confirmed_action(self, action_type: str, target_ids: List[int], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a confirmed action against target IDs"""
        affected_items = []
        
        if action_type == "delete_item":
            for tid in target_ids:
                item = self.db.get_item_by_id(tid)
                if item:
                    success, err = self.action_processor.execute_delete(tid)
                    if not success:
                        return {
                            "success": False,
                            "error": err,
                            "response": f"⚠️ Delete transaction failed: {err}",
                            "action_performed": False
                        }
                    affected_items.append(item)
                    
            lbl = "Item" if len(affected_items) == 1 else "Items"
            return {
                "success": True,
                "response": f"✓ {lbl} deleted successfully.",
                "action_performed": True,
                "action_type": "delete_item",
                "affected_items": affected_items
            }

        elif action_type in ("complete_item", "restore_item"):
            completed_val = (action_type == "complete_item")
            for tid in target_ids:
                success, updated_item, err = self.action_processor.execute_update(tid, {"completed": completed_val})
                if not success:
                    return {
                        "success": False,
                        "error": err,
                        "response": f"⚠️ Completion toggle transaction failed: {err}",
                        "action_performed": False
                    }
                affected_items.append(updated_item)
                
            verb = "Completed" if completed_val else "Restored"
            return {
                "success": True,
                "response": f"✓ Items marked as {verb.lower()}.",
                "action_performed": True,
                "action_type": action_type,
                "affected_items": affected_items
            }

        elif action_type == "update_item":
            update_fields = payload.get("update_fields") or {}
            # Clean fields
            filtered_updates = {k: v for k, v in update_fields.items() if v is not None}
            
            # Handle list tags to string conversion
            if "tags" in filtered_updates and isinstance(filtered_updates["tags"], list):
                filtered_updates["tags"] = ",".join(filtered_updates["tags"])
                
            for tid in target_ids:
                success, updated_item, err = self.action_processor.execute_update(tid, filtered_updates)
                if not success:
                    return {
                        "success": False,
                        "error": err,
                        "response": f"⚠️ Update transaction failed: {err}",
                        "action_performed": False
                    }
                affected_items.append(updated_item)
                
            return {
                "success": True,
                "response": "✓ Items updated successfully.",
                "action_performed": True,
                "action_type": "update_item",
                "affected_items": affected_items
            }
            
        return {
            "success": False,
            "response": "Unknown action type",
            "action_performed": False
        }

    def _fallback_rag_response(self, message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Original AskAuraService search & retrieval pipeline"""
        all_db_items = self.db.get_all_items()
        
        # 1. Semantic Search
        semantic_results = []
        try:
            semantic_results = self.vector_store.search(message, n_results=5)
        except Exception as e:
            print(f"Warning: ChromaDB search failed in AskAuraService: {e}")

        # Resolve semantic items
        retrieved_items = {}
        for res in semantic_results:
            item_id = res['id']
            distance = res.get('distance')
            similarity = 1.0 - distance if distance is not None else 0.0
            
            # Fetch full record from SQLite
            item = self.db.get_item_by_id(item_id)
            if item:
                item['relevance_score'] = similarity
                retrieved_items[item_id] = item

        # 2. SQLite Context Supplementation based on keyword detection
        msg_lower = message.lower()
        today_str = datetime.now().date().isoformat()
        
        needs_today = "today" in msg_lower or "due" in msg_lower
        needs_overdue = "overdue" in msg_lower
        needs_reminders = "reminder" in msg_lower or "reminders" in msg_lower
        needs_notes = "note" in msg_lower or "notes" in msg_lower
        needs_completed = "complete" in msg_lower or "completed" in msg_lower or "done" in msg_lower
        needs_schedule = "schedule" in msg_lower or "calendar" in msg_lower

        for item in all_db_items:
            item_id = item['id']
            if item_id in retrieved_items:
                continue

            item_date_str = item.get('datetime', '').split('T')[0] if item.get('datetime') else ''
            is_completed = bool(item.get('completed', False))

            match = False
            
            if needs_today and item.get('type') in ('task', 'reminder') and not is_completed and item_date_str == today_str:
                match = True
            elif needs_overdue and item.get('type') in ('task', 'reminder') and not is_completed and item_date_str and item_date_str < today_str:
                match = True
            elif needs_reminders and item.get('type') == 'reminder' and not is_completed:
                match = True
            elif needs_notes and item.get('type') == 'note':
                match = True
            elif needs_completed and is_completed:
                match = True
            elif needs_schedule and item.get('datetime') and not is_completed:
                match = True

            if match:
                item['relevance_score'] = 1.0
                retrieved_items[item_id] = item

        # Format Context payload
        context_list = list(retrieved_items.values())
        context_list = sorted(context_list, key=lambda x: x.get('relevance_score', 0.0), reverse=True)[:15]

        # Build sources metadata
        sources = []
        for item in context_list:
            sources.append({
                "id": item["id"],
                "title": item["title"],
                "type": item["type"],
                "relevance_score": item.get("relevance_score", 1.0)
            })

        # Format items as a compact string
        today_formatted = datetime.now().strftime('%A, %B %d, %Y')
        today_date_only = datetime.now().date().isoformat()
        context_str = f"Today's Date: {today_formatted}\n\n"
        
        if context_list:
            context_str += "Retrieved AuraPlan Items:\n"
            for item in context_list:
                item_type = item['type'].upper()
                is_completed = bool(item.get('completed'))
                status = "Completed" if is_completed else "Active"
                due = f", Due: {item.get('datetime')}" if item.get('datetime') else ""
                priority = f", Priority: {item.get('priority')}" if item.get('priority') else ""
                tags = f", Tags: {item.get('tags')}" if item.get('tags') else ""
                desc = f", Description: {item.get('description')}" if item.get('description') else ""

                # Deterministic timing label - computed in Python, not left for the LLM to work out.
                timing = ""
                if item.get('datetime') and not is_completed:
                    item_date_only = item['datetime'].split('T')[0]
                    if item_date_only < today_date_only:
                        timing = " [OVERDUE]"
                    elif item_date_only == today_date_only:
                        timing = " [DUE TODAY]"
                    else:
                        timing = " [UPCOMING]"

                context_str += f"- [{item_type}]{timing} ID: {item['id']}, Title: '{item['title']}', Status: {status}{due}{priority}{tags}{desc}\n"
        else:
            context_str += "No matching tasks, reminders, or notes found in database for this query.\n"

        system_prompt = (
            "You are Aura, the personal productivity assistant for AuraPlan.\n"
            "You help users understand, organize, and prioritize their tasks, reminders, and notes.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. PRIORITIZE RETRIEVED DATA: Always prioritize the retrieved AuraPlan items context over general knowledge.\n"
            "2. GROUNDING & FACTS: Strictly distinguish between facts found in the user's data and suggestions/recommendations you generate. Do not hallucinate or invent items.\n"
            "3. CONCISE & ACTIONABLE: Keep answers direct, friendly, and structured (bullet points are preferred for lists).\n"
            "4. TONE GUIDELINES: Do not give arbitrary directives like 'You should finish DBMS first.' Instead, base recommendations on retrieved data, e.g., 'You currently have an overdue DBMS assignment due on June 23rd. Based on this, you might want to prioritize it.'\n"
            "5. DATE FIDELITY: When citing a due date, priority, or status, you MUST copy it verbatim from the retrieved item's context line above. Never estimate, round, guess, or invent a date.\n"
            "6. TIMING LABELS: Each item is already tagged [OVERDUE], [DUE TODAY], or [UPCOMING] in the context above. Always use that exact tag to describe an item's timing. Do NOT compute or guess whether something is overdue/today/upcoming yourself — trust the provided tag completely."
        )

        history_str = ""
        for chat in history[-6:]:
            role = "User" if chat.get("role") == "user" else "Aura"
            history_str += f"{role}: {chat.get('content')}\n"

        full_prompt = (
            f"{system_prompt}\n\n"
            f"--- CONTEXT ---\n{context_str}\n"
            f"--- CONVERSATION HISTORY ---\n{history_str}"
            f"User: {message}\n"
            f"Aura:"
        )

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 400,
                    "num_ctx": 2048
                }
            },
            timeout=60
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Ollama API returned status code {response.status_code}",
                "sources": []
            }

        reply = response.json().get('response', '').strip()
        
        if not context_list and "no matching" in context_str.lower() and not reply:
            reply = "I couldn't find any items in your workspace matching that description. Try searching for something else or adjusting your query."

        return {
            "success": True,
            "response": reply,
            "sources": sources,
            "action_performed": False
        }