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

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static' / 'visualizations'

# Initialize services
db = Database(Config.DATABASE_PATH)
vector_store = VectorStore()
llm_service = LLMService()
processor = IntentProcessor(db, vector_store)
sync_orchestrator = SyncOrchestrator(db, llm_service, use_mock=Config.USE_MOCK_DATA)
visualizer = DayViewGenerator(output_dir=str(STATIC_DIR))

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

@app.route('/api/search', methods=['POST'])
def search():
    """Semantic search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400
        
        results = vector_store.search(query, n_results=10)
        
        items = []
        for result in results:
            item = db.get_item_by_id(result['id'])
            if item:
                item['relevance_score'] = 1 - result['distance'] if result['distance'] else None
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
        
        grouped = {
            'today': [],
            'tomorrow': [],
            'upcoming': []
        }
        
        print(f"\n Grouping {len(all_items)} items...")
        print(f"   Today: {today}")
        print(f"   Tomorrow: {tomorrow}")
        
        for item in all_items:
            if not item.get('datetime'):
                grouped['upcoming'].append(item)
                continue
            
            try:
                item_date = datetime.fromisoformat(item['datetime']).date()
                
                print(f"   Item: '{item['title'][:30]}' -> Date: {item_date}")
                
                if item_date == today:
                    print(f"Added to TODAY")
                    grouped['today'].append(item)
                elif item_date == tomorrow:
                    print(f"Added to TOMORROW")
                    grouped['tomorrow'].append(item)
                elif item_date > tomorrow:
                    print(f" Added to UPCOMING")
                    grouped['upcoming'].append(item)
                else:
                    print(f" Past date, added to UPCOMING")
                    grouped['upcoming'].append(item)
            except Exception as date_error:
                print(f"Date parse error: {date_error}")
                grouped['upcoming'].append(item)
        
        print(f"\n   Results: Today={len(grouped['today'])}, Tomorrow={len(grouped['tomorrow'])}, Upcoming={len(grouped['upcoming'])}\n")
        
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
    port = int(os.environ.get("PORT", 10000))  
    app.run(debug=False, host='0.0.0.0', port=port)