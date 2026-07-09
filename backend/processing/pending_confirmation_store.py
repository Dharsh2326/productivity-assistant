import time
from typing import Dict, Any, Optional

class PendingConfirmationStore:
    def __init__(self, timeout_seconds: int = 300):
        self.timeout = timeout_seconds
        self.store: Dict[str, Dict[str, Any]] = {}

    def _cleanup(self):
        """Remove expired confirmations"""
        now = time.time()
        expired_keys = [
            key for key, val in self.store.items()
            if now - val["timestamp"] > self.timeout
        ]
        for key in expired_keys:
            del self.store[key]

    def set_pending(self, session_id: str, action_type: str, target_ids: list, payload: Dict[str, Any]) -> None:
        """Store a pending confirmation"""
        self._cleanup()
        self.store[session_id] = {
            "action_type": action_type,
            "target_ids": target_ids,
            "payload": payload,
            "timestamp": time.time()
        }

    def get_pending(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a pending confirmation if it exists and has not expired"""
        self._cleanup()
        if session_id in self.store:
            entry = self.store[session_id]
            if time.time() - entry["timestamp"] <= self.timeout:
                return entry
            else:
                del self.store[session_id]
        return None

    def clear_pending(self, session_id: str) -> None:
        """Clear the pending confirmation for a session"""
        if session_id in self.store:
            del self.store[session_id]
