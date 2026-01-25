import json
import os
from typing import List, Dict
from datetime import datetime
from ingestion.base import DataSource  # Changed

class CalendarSource(DataSource):
    """Calendar event ingestion - CURRENT: Mock data from JSON"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        # Use absolute path from current file location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.mock_file = os.path.join(current_dir, 'mock_data', 'calendar_events.json')
    
    def fetch_data(self) -> List[Dict]:
        """Fetch calendar events"""
        if self.use_mock:
            return self._fetch_mock_data()
        else:
            raise NotImplementedError("Real Google Calendar integration not enabled")
    
    def _fetch_mock_data(self) -> List[Dict]:
        """Load mock calendar events from JSON"""
        if not os.path.exists(self.mock_file):
            print(f"Warning: Mock data file not found: {self.mock_file}")
            return []
        
        with open(self.mock_file, 'r') as f:
            return json.load(f)
    
    def transform_to_items(self, raw_events: List[Dict]) -> List[Dict]:
        """Transform calendar events to standard item format"""
        items = []
        
        for event in raw_events:
            start = event.get('start', {})
            if 'dateTime' in start:
                event_datetime = start['dateTime']
            elif 'date' in start:
                event_datetime = f"{start['date']}T09:00:00"
            else:
                event_datetime = None
            
            attendees = event.get('attendees', [])
            if len(attendees) > 5:
                priority = 'high'
            elif len(attendees) > 0:
                priority = 'medium'
            else:
                priority = 'low'
            
            title = event.get('summary', 'Untitled Event')
            event_type = 'reminder'
            
            if any(word in title.lower() for word in ['birthday', 'anniversary']):
                event_type = 'note'
            elif any(word in title.lower() for word in ['deadline', 'due', 'submit']):
                event_type = 'task'
            
            item = {
                'type': event_type,
                'title': title,
                'description': event.get('description', ''),
                'datetime': event_datetime,
                'priority': priority,
                'tags': ['calendar', 'meeting'],
                'source': 'calendar',
                'external_id': f"cal_{event.get('id')}",
                'completed': False
            }
            
            items.append(item)
        
        return items