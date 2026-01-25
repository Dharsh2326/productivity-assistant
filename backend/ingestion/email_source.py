import json
import os
from typing import List, Dict
from .base import DataSource

class EmailSource(DataSource):
    """
    Email ingestion for task extraction.
    
    CURRENT: Mock data from JSON
    FUTURE: Gmail API or IMAP integration
    
    To enable real Gmail:
    1. Uncomment GmailAPI class below
    2. Add Gmail OAuth credentials
    3. Update Config.USE_MOCK_DATA = False
    """
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.mock_file = 'backend/ingestion/mock_data/email_messages.json'
    
    def fetch_data(self) -> List[Dict]:
        """Fetch emails"""
        if self.use_mock:
            return self._fetch_mock_data()
        else:
            # TODO: Implement real Gmail API
            # return self._fetch_gmail()
            raise NotImplementedError("Real Gmail integration not enabled")
    
    def _fetch_mock_data(self) -> List[Dict]:
        """Load mock emails from JSON"""
        if not os.path.exists(self.mock_file):
            print(f"Warning: Mock data file not found: {self.mock_file}")
            return []
        
        with open(self.mock_file, 'r') as f:
            return json.load(f)
    
    def transform_to_items(self, raw_emails: List[Dict]) -> List[Dict]:
        """
        Transform emails to standard item format.
        
        Note: This is a simple transformation.
        For intelligent extraction, use llm_extraction layer.
        """
        items = []
        
        for email in raw_emails:
            # Basic extraction (LLM will refine this)
            subject = email.get('subject', '')
            
            # Simple classification
            if 'deadline' in subject.lower() or 'submit' in subject.lower():
                item_type = 'task'
                priority = 'high'
            elif 'meeting' in subject.lower() or 'interview' in subject.lower():
                item_type = 'reminder'
                priority = 'high'
            elif 'seminar' in subject.lower() or 'workshop' in subject.lower():
                item_type = 'reminder'
                priority = 'medium'
            else:
                item_type = 'note'
                priority = 'medium'
            
            item = {
                'type': item_type,
                'title': subject[:100],
                'description': email.get('snippet', '')[:300],
                'datetime': None,  # LLM will extract this
                'priority': priority,
                'tags': ['email'],
                'source': 'email',
                'external_id': f"email_{email.get('id')}",
                'completed': False,
                '_raw_email': email  # Keep for LLM processing
            }
            
            items.append(item)
        
        return items
    
    # ========== FUTURE: Real Gmail Implementation ==========
    # 
    # def _fetch_gmail(self) -> List[Dict]:
    #     """
    #     Real Gmail API integration.
    #     
    #     Implementation:
    #     from googleapiclient.discovery import build
    #     from google.oauth2.credentials import Credentials
    #     
    #     creds = Credentials.from_authorized_user_file('backend/gmail_token.json')
    #     service = build('gmail', 'v1', credentials=creds)
    #     
    #     results = service.users().messages().list(
    #         userId='me',
    #         maxResults=20,
    #         q='is:unread newer_than:7d'  # Unread from last 7 days
    #     ).execute()
    #     
    #     messages = results.get('messages', [])
    #     
    #     emails = []
    #     for msg in messages:
    #         message = service.users().messages().get(
    #             userId='me',
    #             id=msg['id'],
    #             format='metadata'
    #         ).execute()
    #         
    #         headers = message['payload']['headers']
    #         subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    #         from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
    #         
    #         # Get snippet
    #         snippet = message.get('snippet', '')
    #         
    #         emails.append({
    #             'id': msg['id'],
    #             'subject': subject,
    #             'from': from_email,
    #             'snippet': snippet,
    #             'date': message.get('internalDate')
    #         })
    #     
    #     return emails
    #     """
    #     pass
    