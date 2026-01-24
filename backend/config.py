import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/productivity.db')
    CHROMA_PATH = os.getenv('CHROMA_PATH', 'data/chroma')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Feature flags (for demo)
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
    
    # Future: Real API credentials (placeholder)
    # GOOGLE_CALENDAR_ENABLED = os.getenv('GOOGLE_CALENDAR_ENABLED', 'false').lower() == 'true'
    # EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    
    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('backend/static/visualizations', exist_ok=True)