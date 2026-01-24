from typing import List, Dict
from ..ingestion.calendar_source import CalendarSource
from ..ingestion.email_source import EmailSource
from ..llm_extraction.llm_service import LLMService
from ..database import Database

class SyncOrchestrator:
    """
    Coordinates data synchronization from multiple sources.
    
    Flow:
    1. Fetch raw data from sources (calendar, email)
    2. Transform to standard format
    3. Use LLM to enhance/refine items
    4. Check for duplicates (external_id)
    5. Save new items
    """
    
    def __init__(self, database: Database, llm_service: LLMService, use_mock=True):
        self.db = database
        self.llm = llm_service
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
        # 1. Fetch raw events
        raw_events = self.calendar_source.fetch_data()
        
        # 2. Transform to standard format
        items = self.calendar_source.transform_to_items(raw_events)
        
        # 3. Save (skip duplicates)
        count = 0
        for item in items:
            # Check if already exists
            existing = self.db.get_item_by_external_id(item['external_id'])
            
            if not existing:
                self.db.create_item(item)
                count += 1
        
        return count
    
    def sync_email(self) -> int:
        """Sync email-based tasks"""
        # 1. Fetch raw emails
        raw_emails = self.email_source.fetch_data()
        
        # 2. Transform to basic format
        items = self.email_source.transform_to_items(raw_emails)
        
        # 3. Use LLM to enhance each item
        count = 0
        for item in items:
            # Check if already exists
            existing = self.db.get_item_by_external_id(item['external_id'])
            
            if existing:
                continue
            
            # Use LLM to extract datetime, refine title, etc.
            raw_email = item.pop('_raw_email', {})
            llm_result = self.llm.extract_from_email(raw_email)
            
            if llm_result.get('success') and llm_result['data'].get('relevant'):
                # Merge LLM enhancements
                enhanced_data = llm_result['data']
                item['title'] = enhanced_data.get('title', item['title'])
                item['description'] = enhanced_data.get('description', item['description'])
                item['datetime'] = enhanced_data.get('datetime', item['datetime'])
                item['priority'] = enhanced_data.get('priority', item['priority'])
                item['type'] = enhanced_data.get('type', item['type'])
                
                self.db.create_item(item)
                count += 1
        
        return count