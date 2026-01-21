import json
import requests
from .config import Config
from backend.prompt import get_system_prompt, get_user_prompt

class LLMService:
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
    
    def parse_natural_language(self, user_input: str) -> dict:
        """
        Send natural language input to Ollama and get structured JSON back
        """
        try:
            # Prepare the prompt
            full_prompt = f"{get_system_prompt()}\n\n{get_user_prompt(user_input)}"
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Ollama API error",
                    "details": f"Status code: {response.status_code}"
                }
            
            # Extract response
            ollama_response = response.json()
            response_text = ollama_response.get('response', '')
            
            # Clean the response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            # Validate structure
            if 'items' not in parsed:
                if 'type' in parsed and 'title' in parsed:
                    parsed = {'items': [parsed]}
                else:
                    return {
                        "success": False,
                        "error": "Invalid JSON structure",
                        "details": "Missing 'items' array"
                    }
            
            return {
                "success": True,
                "data": parsed,
                "raw_response": response_text
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Cannot connect to Ollama",
                "details": "Make sure Ollama is running (ollama serve)"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Ollama request timeout",
                "details": "Request took too long"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "Failed to parse LLM response as JSON",
                "details": str(e),
                "raw_response": response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": "LLM service error",
                "details": str(e)
            }