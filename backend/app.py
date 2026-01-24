from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta

from .config import Config
from .database import Database
from .vector_store import VectorStore
from .llm_extraction.llm_service import LLMService
from .processing.intent_processor import IntentProcessor
from .processing.sync_orchestrator import SyncOrchestrator
from .visualizer.day_view_generator import DayViewGenerator

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize services
db = Database(Config.DATABASE_PATH)
vector_store = VectorStore()
llm_service = LLMService()
processor = IntentProcessor(db, vector_store)
sync_orchestrator = SyncOrchestrator(db, llm_service, use_mock=Config.USE_MOCK_DATA)
visualizer = DayViewGenerator()

# ===== EXISTING ENDPOINTS =====

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "message": "Productivity Assistant API is running",
        "features": {
            "mock_data": Config.USE_MOCK_DATA,
            "llm_model": Config.OLLAMA_MODEL
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
        
        llm_result = llm_service.parse_natural_language(user_input)
        
        if not llm_result['success']:
            return jsonify({
                "success": False,
                "error": llm_result.get('error', 'LLM processing failed'),
                "details": llm_result.get('details', '')
            }), 500
        
        items = llm_result['data'].get('items', [])
        if not items:
            return jsonify({
                "success": False,
                "error": "No items extracted from input",
                "details": "LLM did not extract any items from your input"
            }), 400
        
        # Validate items before processing
        validated_items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if 'type' not in item or 'title' not in item:
                continue
            # Ensure required fields
            validated_item = {
                'type': item.get('type', 'task'),
                'title': item.get('title', 'Untitled'),
                'description': item.get('description'),
                'datetime': item.get('datetime'),
                'priority': item.get('priority', 'medium'),
                'tags': item.get('tags', []),
                'completed': item.get('completed', False)
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
    item_type = request.args.get('type')
    items = db.get_all_items(item_type)
    
    return jsonify({
        "success": True,
        "items": items,
        "count": len(items)
    })

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get single item"""
    item = db.get_item_by_id(item_id)
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({
        "success": True,
        "item": item
    })

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update item"""
    data = request.get_json()
    
    success = db.update_item(item_id, data)
    
    if not success:
        return jsonify({"error": "Item not found"}), 404
    
    updated_item = db.get_item_by_id(item_id)
    
    return jsonify({
        "success": True,
        "item": updated_item
    })

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete item"""
    vector_store.delete_item(item_id)
    success = db.delete_item(item_id)
    
    if not success:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "Item deleted"
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Semantic search"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
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

# ===== NEW ENDPOINTS =====

@app.route('/api/sync', methods=['POST'])
def sync_external_data():
    """
    Sync calendar and email data.
    
    CURRENT: Uses mock data from JSON files
    FUTURE: Will call real APIs when Config.USE_MOCK_DATA = False
    """
    try:
        result = sync_orchestrator.sync_all()
        
        return jsonify({
            'success': True,
            'synced': result,
            'message': f"Synced {result['total']} items"
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/items/grouped', methods=['GET'])
def get_items_grouped():
    """Get items grouped by day (today/tomorrow/upcoming)"""
    view = request.args.get('view', 'all')
    
    all_items = db.get_all_items()
    
    today = datetime.now().date()
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    grouped = {
        'today': [],
        'tomorrow': [],
        'upcoming': []
    }
    
    for item in all_items:
        if not item.get('datetime'):
            grouped['upcoming'].append(item)
            continue
        
        try:
            item_date = datetime.fromisoformat(item['datetime']).date()
            
            if item_date == today:
                grouped['today'].append(item)
            elif item_date == tomorrow:
                grouped['tomorrow'].append(item)
            elif item_date > tomorrow:
                grouped['upcoming'].append(item)
        except:
            grouped['upcoming'].append(item)
    
    if view == 'all':
        return jsonify({'success': True, 'items': grouped})
    else:
        return jsonify({'success': True, 'items': grouped.get(view, [])})

@app.route('/api/visualize/day', methods=['POST'])
def visualize_day():
    """Generate visual day view image"""
    try:
        data = request.get_json() or {}
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get items for that day
        start_datetime = f"{date}T00:00:00"
        end_datetime = f"{date}T23:59:59"
        
        day_items = db.get_items_by_date_range(start_datetime, end_datetime)
        
        # Ensure items have source field (default to 'manual' if missing)
        for item in day_items:
            if 'source' not in item:
                item['source'] = 'manual'
            if 'priority' not in item:
                item['priority'] = 'medium'
        
        # Generate image
        image_url = visualizer.generate(date, day_items)
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'date': date,
            'items_count': len(day_items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/static/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve generated visualizations"""
    return send_from_directory('backend/static/visualizations', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
