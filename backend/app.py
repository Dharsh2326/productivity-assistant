from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.database import Database
from backend.vector_store import VectorStore
from backend.llm_service import LLMService
from backend.intent_processor import IntentProcessor

app = Flask(__name__)
CORS(app)

# Initialize services
db = Database(Config.DATABASE_PATH)
vector_store = VectorStore()
llm_service = LLMService()
processor = IntentProcessor(db, vector_store)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Productivity Assistant API is running"})

@app.route('/api/parse', methods=['POST'])
def parse_input():
    """Parse natural language input and create items"""
    data = request.get_json()
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    # Call LLM
    llm_result = llm_service.parse_natural_language(user_input)
    
    if not llm_result['success']:
        return jsonify(llm_result), 500
    
    # Process and store items
    items = llm_result['data'].get('items', [])
    created_items = processor.process_items(items)
    
    return jsonify({
        "success": True,
        "items": created_items,
        "count": len(created_items)
    })

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items, optionally filtered by type"""
    item_type = request.args.get('type')
    items = db.get_all_items(item_type)
    
    return jsonify({
        "success": True,
        "items": items,
        "count": len(items)
    })

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a single item by ID"""
    item = db.get_item_by_id(item_id)
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({
        "success": True,
        "item": item
    })

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an item"""
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
    """Delete an item"""
    # Delete from vector store
    vector_store.delete_item(item_id)
    
    # Delete from database
    success = db.delete_item(item_id)
    
    if not success:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "Item deleted"
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Semantic search for items"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Search vector store
    results = vector_store.search(query, n_results=10)
    
    # Get full items from database
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)