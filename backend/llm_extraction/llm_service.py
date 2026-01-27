import json
import requests
from typing import Dict
from config import Config
from llm_extraction.prompts import get_system_prompt, get_user_prompt, get_email_extraction_prompt

class LLMService:
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
    
    def parse_natural_language(self, user_input: str) -> dict:
        """Send natural language input to Ollama and get structured JSON back"""
        try:
            full_prompt = f"{get_system_prompt()}\n\n{get_user_prompt(user_input)}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200,  # INCREASED: Was 100, now 200 for complete JSON
                        "num_ctx": 1024,     # INCREASED: Was 512, now 1024 for better understanding
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=45  # INCREASED: Give more time (was 15, now 45 seconds)
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Ollama API error",
                    "details": f"Status code: {response.status_code}"
                }
            
            ollama_response = response.json()
            response_text = ollama_response.get('response', '')
            
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            parsed = json.loads(response_text)
            
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
                "details": "Request took too long (>45s). Try a simpler query or use a faster model."
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
    
    def extract_from_email(self, email_data: Dict) -> dict:
        """Extract task/reminder from email using LLM"""
        prompt = get_email_extraction_prompt(
            email_data.get('subject', ''),
            email_data.get('snippet', '')
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1, 
                        "num_predict": 100,
                        "num_ctx": 512
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result_text = response.json().get('response', '{}')
                result_text = result_text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                
                result = json.loads(result_text)
                
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {"success": False, "error": "LLM request failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}