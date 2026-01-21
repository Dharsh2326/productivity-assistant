import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/productivity.db')
    CHROMA_PATH = os.getenv('CHROMA_PATH', 'data/chroma')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)