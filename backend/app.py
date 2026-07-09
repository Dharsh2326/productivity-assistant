from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from pathlib import Path

from config import Config
from database import Database
from vector_store import VectorStore
from llm_extraction.llm_service import LLMService
from processing.intent_processor import IntentProcessor
from processing.sync_orchestrator import SyncOrchestrator
from visualizer.day_view_generator import DayViewGenerator
from processing.ask_aura_service import AskAuraService

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static' / 'visualizations'

# Initialize services
db = Database(Config.DATABASE_PATH)
vector_store = VectorStore()
llm_service = LLMService()
processor = IntentProcessor(db, vector_store)
sync_orchestrator = SyncOrchestrator(db, llm_service, vector_store=vector_store, use_mock=Config.USE_MOCK_DATA)
visualizer = DayViewGenerator(output_dir=str(STATIC_DIR))
ask_aura_service = AskAuraService(db, vector_store)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Productivity Assistant API is running",
        "features": {
            "mock_data": Config.USE_MOCK_DATA,
            "llm_model": Config.OLLAMA_MODEL
        },
        "database": {
            "path": Config.DATABASE_PATH,
            "exists": os.path.exists(Config.DATABASE_PATH)
        }
    })

@app.route('/api/parse', methods=['POST'])
def parse_input():
    """Parse natural language input (manual entry)"""
    try:
        data = request.get_json()
        user_input = data.get('input', '')
        
        if not user_input:
            return jsonify({"success": False, "error": "No input provided"}), 400
        
        print(f"Parsing input: '{user_input}'")
        llm_result = llm_service.parse_natural_language(user_input)
        print(f" LLM result: {llm_result.get('success')}")
        
        if not llm_result['success']:
            print(f" LLM failed: {llm_result.get('error')}")
            print(f"   Details: {llm_result.get('details')}")
            return jsonify({
                "success": False,
                "error": llm_result.get('error', 'LLM processing failed'),
                "details": llm_result.get('details', '')
            }), 500
        
        items = llm_result['data'].get('items', [])
        print(f" Extracted {len(items)} items")
        
        if not items:
            print("No items extracted from LLM response")
            return jsonify({
                "success": False,
                "error": "No items extracted from input",
                "details": "LLM did not extract any items from your input"
            }), 400
        
        # Validate and normalize items
        validated_items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if 'type' not in item or 'title' not in item:
                continue
            
            validated_item = {
                'type': item.get('type', 'task'),
                'title': item.get('title', 'Untitled'),
                'description': item.get('description'),
                'datetime': item.get('datetime'),
                'priority': item.get('priority', 'medium'),
                'tags': item.get('tags', []),
                'completed': item.get('completed', False),
                'source': 'manual'
            }
            validated_items.append(validated_item)
        
        if not validated_items:
            return jsonify({
                "success": False,
                "error": "Invalid item structure",
                "details": "Items must have 'type' and 'title' fields"
            }), 400
        
        created_items = processor.process_items(validated_items)
        
        return jsonify({
            "success": True,
            "items": created_items,
            "count": len(created_items)
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in parse_input: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            "success": False,
            "error": "Server error",
            "details": str(e)
        }), 500

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items"""
    try:
        item_type = request.args.get('type')
        items = db.get_all_items(item_type)
        
        return jsonify({
            "success": True,
            "items": items,
            "count": len(items)
        })
    except Exception as e:
        print(f"Error getting items: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get single item"""
    try:
        item = db.get_item_by_id(item_id)
        
        if not item:
            return jsonify({"success": False, "error": "Item not found"}), 404
        
        return jsonify({
            "success": True,
            "item": item
        })
    except Exception as e:
        print(f"Error getting item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update item"""
    try:
        data = request.get_json()
        success = db.update_item(item_id, data)
        
        if not success:
            return jsonify({"success": False, "error": "Item not found"}), 404
        
        updated_item = db.get_item_by_id(item_id)
        
        # Sync with Chroma vector store
        if updated_item:
            try:
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
                vector_store.add_item(item_id, search_text, metadata)
            except Exception as vec_error:
                print(f"Warning: Failed to update vector store during PUT: {vec_error}")
        
        return jsonify({
            "success": True,
            "item": updated_item
        })
    except Exception as e:
        print(f" Error updating item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete item"""
    try:
        vector_store.delete_item(item_id)
        success = db.delete_item(item_id)
        
        if not success:
            return jsonify({"success": False, "error": "Item not found"}), 404
        
        return jsonify({
            "success": True,
            "message": "Item deleted"
        })
    except Exception as e:
        print(f"Error deleting item: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ask-aura', methods=['POST'])
def ask_aura():
    """Ask Aura conversational assistant"""
    try:
        data = request.get_json() or {}
        message = data.get('message', '')
        history = data.get('history', [])
        session_id = data.get('session_id', 'default_session')
        confirm_action = data.get('confirm_action', None)  # 'confirm' or 'cancel'
        
        if not message and confirm_action is None:
            return jsonify({"success": False, "error": "No message or confirmation provided"}), 400
            
        print(f"Ask Aura query: '{message}' | History length: {len(history)} | Session: {session_id} | Confirm: {confirm_action}")
        result = ask_aura_service.get_assistant_response(
            message=message,
            history=history,
            session_id=session_id,
            confirm_action=confirm_action
        )
        
        if not result.get('success', False):
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate response'),
                "response": result.get('error', 'Failed to generate response'),
                "sources": [],
                "action_performed": False
            })
            
        # Return complete action rich JSON structure
        return jsonify({
            "success": True,
            "response": result.get('response'),
            "sources": result.get('sources', []),
            "action_performed": result.get('action_performed', False),
            "action_type": result.get('action_type', None),
            "affected_items": result.get('affected_items', []),
            "pending_confirmation": result.get('pending_confirmation', None),
            "ambiguous_matches": result.get('ambiguous_matches', None)
        })
    except Exception as e:
        print(f"Error in /api/ask-aura: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error occurred",
            "response": "An internal server error occurred. Please try again.",
            "sources": [],
            "action_performed": False
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Semantic search"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '')
        
        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400
        
        # Support metadata filtering
        where_filter = data.get('where', {}) or {}
        
        # Parse exclude_completed (defaults to True)
        exclude_completed = data.get('exclude_completed', True)
        if isinstance(exclude_completed, str):
            exclude_completed = exclude_completed.lower() == 'true'
            
        if exclude_completed:
            where_filter["completed"] = False
            
        results = vector_store.search(query, n_results=10, where=where_filter)
        
        items = []
        for result in results:
            distance = result.get('distance')
            similarity = 1.0 - distance if distance is not None else 0.0
            
            item = db.get_item_by_id(result['id'])
            title = item.get('title', 'Unknown') if item else 'Unknown'
            
            # Logging requirement: Print query, item id, title, similarity score
            print(f"Query: {query} | Item ID: {result['id']} | Title: {title} | Similarity Score: {similarity}")
            
            # Apply similarity threshold
            if similarity >= Config.SEARCH_SIMILARITY_THRESHOLD:
                if item:
                    item['relevance_score'] = similarity
                    items.append(item)
        
        return jsonify({
            "success": True,
            "query": query,
            "items": items,
            "count": len(items)
        })
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync_external_data():
    """Sync calendar and email data"""
    try:
        print("Starting sync...")
        result = sync_orchestrator.sync_all()
        print(f"Sync complete: {result}")
        
        return jsonify({
            'success': True,
            'synced': result,
            'message': f"Synced {result['total']} items ({result['calendar']} calendar + {result['email']} email)"
        })
    except Exception as e:
        print(f"Sync error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/items/grouped', methods=['GET'])
def get_items_grouped():
    """Get items grouped by day (today/tomorrow/upcoming)"""
    try:
        view = request.args.get('view', 'all')
        all_items = db.get_all_items()
        
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        local_tz = datetime.now().astimezone().tzinfo
        
        grouped = {
            'overdue': [],
            'today': [],
            'tomorrow': [],
            'upcoming': []
        }
        
        print(f"\n--- Grouping Diagnostics ---")
        print(f"Current local date: {today}")
        print(f"Current local timezone: {local_tz}")
        
        for item in all_items:
            dt_str = item.get('datetime')
            if not dt_str:
                print(f"Item ID: {item.get('id')} | Datetime: None | Parsed: None | Assigned: none")
                continue
            
            try:
                dt = datetime.fromisoformat(dt_str)
                if dt.tzinfo is not None:
                    dt = dt.astimezone(local_tz)
                item_date = dt.date()
                
                assigned_buckets = []
                # Overdue: incomplete items with due date before today
                if item_date < today:
                    if not bool(item.get('completed')):
                        grouped['overdue'].append(item)
                        assigned_buckets.append('overdue')
                elif item_date == today:
                    grouped['today'].append(item)
                    assigned_buckets.append('today')
                elif item_date == tomorrow:
                    grouped['tomorrow'].append(item)
                    assigned_buckets.append('tomorrow')
                
                # Upcoming contains tomorrow and all future dates (> today)
                if item_date > today:
                    grouped['upcoming'].append(item)
                    assigned_buckets.append('upcoming')
                
                assigned_str = "/".join(assigned_buckets) if assigned_buckets else "none"
                print(f"Item ID: {item.get('id')} | Datetime: {dt_str} | Parsed: {item_date} | Assigned: {assigned_str}")
            except Exception as date_error:
                print(f"Item ID: {item.get('id')} | Datetime: {dt_str} | Parsed error: {date_error} | Assigned: none")
        
        print("----------------------------\n")
        
        if view == 'all':
            return jsonify({'success': True, 'items': grouped})
        else:
            return jsonify({'success': True, 'items': grouped.get(view, [])})
    except Exception as e:
        print(f"Error in get_items_grouped: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/visualize/day', methods=['POST'])
def visualize_day():
    """Generate visual day view image"""
    try:
        data = request.get_json() or {}
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        print(f"Generating visualization for {date}...")
        
        start_datetime = f"{date}T00:00:00"
        end_datetime = f"{date}T23:59:59"
        
        day_items = db.get_items_by_date_range(start_datetime, end_datetime)
        print(f"Found {len(day_items)} items for {date}")
        
        # Generate image
        image_url = visualizer.generate(date, day_items)
        print(f"Generated image: {image_url}")
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'date': date,
            'items_count': len(day_items)
        })
    except Exception as e:
        print(f"Visualization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/static/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve generated visualizations"""
    try:
        return send_from_directory(str(STATIC_DIR), filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting Productivity Assistant API")
    print("="*60)
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"ChromaDB: {Config.CHROMA_PATH}")
    print(f"Mock Data: {Config.USE_MOCK_DATA}")
    print(f"LLM Model: {Config.OLLAMA_MODEL}")
    print(f"Static Files: {STATIC_DIR}")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')