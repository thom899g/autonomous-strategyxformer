"""
Robust logging system for Autonomous StrategyXformer
Integrates with Firebase for centralized log management
"""
import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import traceback
from firebase_admin import firestore

class FirebaseLogHandler(logging.Handler):
    """Custom log handler for Firebase Firestore"""
    
    def __init__(self, firestore_client):
        super().__init__()
        self.firestore_client = firestore_client
        self.collection_name = 'system_logs'
        self.batch_size = 10
        self._buffer = []
        
    def emit(self, record):
        """Emit log record to Firebase"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'message': self.format(record),
                'exception': record.exc_info[-1].__name__ if record.exc_info else None
            }
            
            # Add to buffer
            self._buffer.append(log_entry)
            
            # Flush if buffer is full
            if len(self._buffer) >= self.batch_size:
                self._flush_buffer()
                
        except Exception as e:
            # Fallback to console if Firebase fails
            print(f"Firebase log failed: {str(e)}", file=sys.stderr)
            
    def _flush_buffer(self):
        """Flush buffered logs to Firebase"""
        try:
            batch = self.firestore_client.batch()
            
            for log_entry in self._buffer:
                doc