import requests
import json
from datetime import datetime
from typing import List, Dict, Any
from config import Config
from database import Database
from vector_store import VectorStore

class AskAuraService:
    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL

    def get_assistant_response(self, message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process the user query: retrieve relevant items, build context, query Ollama,
        and return the response with sources.
        """
        try:
            # Check if database has any items at all
            all_db_items = self.db.get_all_items()
            if not all_db_items:
                return {
                    "success": True,
                    "response": "Your AuraPlan workspace is currently empty! You can start by adding tasks, notes, or reminders using the input box above (e.g., 'Submit project report tomorrow at 5 PM' or 'Note: DBMS Normalization is important'). Once you add some items, I'll be able to help you manage, summarize, and prioritize your workload.",
                    "sources": []
                }

            # 1. Semantic Search (Top 5 results)
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
            
            # Detect intents
            needs_today = "today" in msg_lower or "due" in msg_lower
            needs_overdue = "overdue" in msg_lower
            needs_reminders = "reminder" in msg_lower or "reminders" in msg_lower
            needs_notes = "note" in msg_lower or "notes" in msg_lower
            needs_completed = "complete" in msg_lower or "completed" in msg_lower or "done" in msg_lower
            needs_schedule = "schedule" in msg_lower or "calendar" in msg_lower

            # Helper lists of database items
            for item in all_db_items:
                item_id = item['id']
                if item_id in retrieved_items:
                    continue  # Already pulled via semantic search

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
                    item['relevance_score'] = 1.0  # Contextually exact match
                    retrieved_items[item_id] = item

            # 3. Format Context payload
            context_list = list(retrieved_items.values())
            
            # Limit context list size to top 15 items overall to avoid token bloating
            context_list = sorted(context_list, key=lambda x: x.get('relevance_score', 0.0), reverse=True)[:15]

            # Build sources metadata for UI
            sources = []
            for item in context_list:
                # Only include as source if it has relatively high relevance
                # or if it was pulled contextually
                sources.append({
                    "id": item["id"],
                    "title": item["title"],
                    "type": item["type"],
                    "relevance_score": item.get("relevance_score", 1.0)
                })

            # Format items as a compact string
            today_formatted = datetime.now().strftime('%A, %B %d, %Y')
            context_str = f"Today's Date: {today_formatted}\n\n"
            
            if context_list:
                context_str += "Retrieved AuraPlan Items:\n"
                for item in context_list:
                    item_type = item['type'].upper()
                    status = "Completed" if item.get('completed') else "Active"
                    due = f", Due: {item.get('datetime')}" if item.get('datetime') else ""
                    priority = f", Priority: {item.get('priority')}" if item.get('priority') else ""
                    tags = f", Tags: {item.get('tags')}" if item.get('tags') else ""
                    desc = f", Description: {item.get('description')}" if item.get('description') else ""
                    
                    context_str += f"- [{item_type}] ID: {item['id']}, Title: '{item['title']}', Status: {status}{due}{priority}{tags}{desc}\n"
            else:
                context_str += "No matching tasks, reminders, or notes found in database for this query.\n"

            # 4. Construct Prompts (Context Awareness & Grounding)
            system_prompt = (
                "You are Aura, the personal productivity assistant for AuraPlan.\n"
                "You help users understand, organize, and prioritize their tasks, reminders, and notes.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. PRIORITIZE RETRIEVED DATA: Always prioritize the retrieved AuraPlan items context over general knowledge.\n"
                "2. GROUNDING & FACTS: Strictly distinguish between facts found in the user's data and suggestions/recommendations you generate. Do not hallucinate or invent items.\n"
                "3. CONCISE & ACTIONABLE: Keep answers direct, friendly, and structured (bullet points are preferred for lists).\n"
                "4. TONE GUIDELINES: Do not give arbitrary directives like 'You should finish DBMS first.' Instead, base recommendations on retrieved data, e.g., 'You currently have an overdue DBMS assignment due on June 23rd. Based on this, you might want to prioritize it.'\n"
                "5. READ-ONLY SCOPE: You cannot create, edit, delete, or toggle completion on items. If requested to do so, politely explain that you are currently in read-only assistant mode and that they can use the dashboard interfaces to make updates."
            )

            # Build user prompt with chat history
            history_str = ""
            for chat in history[-6:]:  # Send last 6 messages to keep context window compact
                role = "User" if chat.get("role") == "user" else "Aura"
                history_str += f"{role}: {chat.get('content')}\n"

            full_prompt = (
                f"{system_prompt}\n\n"
                f"--- CONTEXT ---\n{context_str}\n"
                f"--- CONVERSATION HISTORY ---\n{history_str}"
                f"User: {message}\n"
                f"Aura:"
            )

            # 5. Call Ollama API
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
                timeout=30
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Ollama API returned status code {response.status_code}",
                    "sources": []
                }

            reply = response.json().get('response', '').strip()
            
            # If no relevant items were found and the response is empty/generic, handle it
            if not context_list and "no matching" in context_str.lower() and not reply:
                reply = "I couldn't find any items in your workspace matching that description. Try searching for something else or adjusting your query."

            return {
                "success": True,
                "response": reply,
                "sources": sources
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "I cannot connect to my brain (Ollama). Please verify that the local Ollama server is running (e.g., `ollama serve`).",
                "sources": []
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "My thought process timed out. Please try a simpler request or verify your local Ollama performance.",
                "sources": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"An error occurred while answering your question: {str(e)}",
                "sources": []
            }
