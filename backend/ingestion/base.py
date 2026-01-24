from abc import ABC, abstractmethod
from typing import List, Dict

class DataSource(ABC):
    """
    Abstract base class for data ingestion.
    
    Future implementations:
    - GoogleCalendarSource (OAuth)
    - GmailSource (OAuth)
    - OutlookCalendarSource
    - etc.
    """
    
    @abstractmethod
    def fetch_data(self) -> List[Dict]:
        """
        Fetch raw data from source.
        
        Returns:
            List of raw data items (format varies by source)
        """
        pass
    
    @abstractmethod
    def transform_to_items(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transform source-specific format to our standard item format.
        
        Standard item format:
        {
            'type': 'task|note|reminder',
            'title': str,
            'description': str,
            'datetime': ISO8601 string or None,
            'priority': 'low|medium|high',
            'tags': List[str],
            'source': 'manual|calendar|email',
            'external_id': str,
            'completed': bool
        }
        """
        pass