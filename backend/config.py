import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
ENV = os.getenv("ENV", "local")  # local | production
IS_PRODUCTION = ENV == "production"

class Config:
    # Get base directory (where config.py is located)
    BASE_DIR = Path(__file__).resolve().parent
    
    # Ollama Configuration
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'data' / 'productivity.db'))
    CHROMA_PATH = os.getenv('CHROMA_PATH', str(BASE_DIR / 'data' / 'chroma'))
    
    # Flask Configuration
    FLASK_ENV = "production" if IS_PRODUCTION else "development"

    FLASK_DEBUG = not IS_PRODUCTION

    # Feature Flags
    USE_MOCK_DATA = not IS_PRODUCTION
    USE_VECTOR_STORE = not IS_PRODUCTION

    
    # Ensure all required directories exist
    @classmethod
    def init_directories(cls):
        """Create required directories based on environment"""
        directories = [
            Path(cls.DATABASE_PATH).parent,  # data/
            cls.BASE_DIR / 'static' / 'visualizations'
        ]

        if not IS_PRODUCTION:
            directories.extend([
                Path(cls.CHROMA_PATH),
                cls.BASE_DIR / 'ingestion' / 'mock_data'
            ])
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f" Ensured directory exists: {directory}")
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        # Check Ollama configuration
        if not IS_PRODUCTION:
            if not cls.OLLAMA_BASE_URL:
                errors.append("OLLAMA_BASE_URL is not set")

            if not cls.OLLAMA_MODEL:
                errors.append("OLLAMA_MODEL is not set")

        
        # Check if mock data files exist when using mock mode
        if cls.USE_MOCK_DATA:
            mock_calendar = cls.BASE_DIR / 'ingestion' / 'mock_data' / 'calendar_events.json'
            mock_email = cls.BASE_DIR / 'ingestion' / 'mock_data' / 'email_messages.json'
            
            if not mock_calendar.exists():
                errors.append(f"Mock calendar data not found: {mock_calendar}")
            
            if not mock_email.exists():
                errors.append(f"Mock email data not found: {mock_email}")
        
        if errors:
            print("\n Configuration Warnings:")
            for error in errors:
                print(f"   - {error}")
            print()
        
        return len(errors) == 0
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        print(f"Base Directory: {cls.BASE_DIR}")
        print(f"Database Path: {cls.DATABASE_PATH}")
        print(f"ChromaDB Path: {cls.CHROMA_PATH}")
        print(f"Ollama URL: {cls.OLLAMA_BASE_URL}")
        print(f"Ollama Model: {cls.OLLAMA_MODEL}")
        print(f"Mock Data Mode: {cls.USE_MOCK_DATA}")
        print(f"Flask Environment: {cls.FLASK_ENV}")
        print("="*60 + "\n")


# Initialize directories on import
Config.init_directories()