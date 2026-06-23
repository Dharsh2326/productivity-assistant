from typing import List, Dict
from ingestion.calendar_source import CalendarSource  
from ingestion.email_source import EmailSource  
from llm_extraction.llm_service import LLMService  
from database import Database 

class SyncOrchestrator:
    def __init__(self, database: Database, llm_service: LLMService, vector_store=None, use_mock=True):
        self.db = database
        self.llm = llm_service
        self.vector_store = vector_store
        self.calendar_source = CalendarSource(use_mock=use_mock)
        self.email_source = EmailSource(use_mock=use_mock)
    
    def sync_all(self) -> Dict:
        """Sync all sources"""
        calendar_count = self.sync_calendar()
        email_count = self.sync_email()
        
        return {
            'calendar': calendar_count,
            'email': email_count,
            'total': calendar_count + email_count
        }
    
    def sync_calendar(self) -> int:
        """Sync calendar events"""
        raw_events = self.calendar_source.fetch_data()
        items = self.calendar_source.transform_to_items(raw_events)
        
        count = 0
        for item in items:
            existing = self.db.get_item_by_external_id(item['external_id'])
            if not existing:
                item_id = self.db.create_item(item)
                count += 1
                if self.vector_store:
                    try:
                        search_text = f"{item.get('title', '')} {item.get('description', '') or ''} {' '.join(item.get('tags', []) or [])}"
                        metadata = {
                            'type': item.get('type', 'task'),
                            'priority': item.get('priority', 'medium'),
                            'tags': ','.join(item.get('tags', [])) if isinstance(item.get('tags'), list) else item.get('tags', ''),
                            'completed': bool(item.get('completed', False))
                        }
                        self.vector_store.add_item(item_id, search_text, metadata)
                    except Exception as vec_error:
                        print(f"Warning: Failed to index synced calendar item: {vec_error}")
        
        return count
    
    def sync_email(self) -> int:
        """Sync email-based tasks"""
        raw_emails = self.email_source.fetch_data()
        items = self.email_source.transform_to_items(raw_emails)
        
        count = 0
        for item in items:
            existing = self.db.get_item_by_external_id(item['external_id'])
            if existing:
                continue
            
            raw_email = item.pop('_raw_email', {})
            llm_result = self.llm.extract_from_email(raw_email)
            
            if llm_result.get('success') and llm_result['data'].get('relevant'):
                enhanced_data = llm_result['data']
                item['title'] = enhanced_data.get('title', item['title'])
                item['description'] = enhanced_data.get('description', item['description'])
                item['datetime'] = enhanced_data.get('datetime', item['datetime'])
                item['priority'] = enhanced_data.get('priority', item['priority'])
                item['type'] = enhanced_data.get('type', item['type'])
                
                item_id = self.db.create_item(item)
                count += 1
                if self.vector_store:
                    try:
                        search_text = f"{item.get('title', '')} {item.get('description', '') or ''} {' '.join(item.get('tags', []) or [])}"
                        metadata = {
                            'type': item.get('type', 'task'),
                            'priority': item.get('priority', 'medium'),
                            'tags': ','.join(item.get('tags', [])) if isinstance(item.get('tags'), list) else item.get('tags', ''),
                            'completed': bool(item.get('completed', False))
                        }
                        self.vector_store.add_item(item_id, search_text, metadata)
                    except Exception as vec_error:
                        print(f"Warning: Failed to index synced email item: {vec_error}")
        
        return count