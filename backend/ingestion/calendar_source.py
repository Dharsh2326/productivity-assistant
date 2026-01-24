import json
import os
from typing import List, Dict
from datetime import datetime
from .base import DataSource

class CalendarSource(DataSource):
    """
    Calendar event ingestion.
    
    CURRENT: Mock data from JSON
    FUTURE: Google Calendar API integration
    
    To enable real Google Calendar:
    1. Uncomment GoogleCalendarAPI class below
    2. Add credentials.json and token.json
    3. Update Config.USE_MOCK_DATA = False
    """
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.mock_file = 'backend/ingestion/mock_data/calendar_events.json'
    
    def fetch_data(self) -> List[Dict]:
        """Fetch calendar events"""
        if self.use_mock:
            return self._fetch_mock_data()
        else:
            # TODO: Implement real Google Calendar API
            # return self._fetch_google_calendar()
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
            # Extract datetime
            start = event.get('start', {})
            if 'dateTime' in start:
                event_datetime = start['dateTime']
            elif 'date' in start:
                # All-day event
                event_datetime = f"{start['date']}T09:00:00"
            else:
                event_datetime = None
            
            # Determine priority based on attendees
            attendees = event.get('attendees', [])
            if len(attendees) > 5:
                priority = 'high'
            elif len(attendees) > 0:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Detect event type from title
            title = event.get('summary', 'Untitled Event')
            event_type = 'reminder'  # Default
            
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
    
    # ========== FUTURE: Real Google Calendar Implementation ==========
    # 
    # def _fetch_google_calendar(self) -> List[Dict]:
    #     """
    #     Real Google Calendar API integration.
    #     
    #     Implementation:
    #     from google.oauth2.credentials import Credentials
    #     from googleapiclient.discovery import build
    #     
    #     creds = Credentials.from_authorized_user_file('backend/token.json')
    #     service = build('calendar', 'v3', credentials=creds)
    #     
    #     now = datetime.utcnow().isoformat() + 'Z'
    #     events_result = service.events().list(
    #         calendarId='primary',
    #         timeMin=now,
    #         maxResults=50,
    #         singleEvents=True,
    #         orderBy='startTime'
    #     ).execute()
    #     
    #     return events_result.get('items', [])
    #     """
    #     pass