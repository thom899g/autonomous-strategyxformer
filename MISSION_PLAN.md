# Autonomous StrategyXformer

## Objective
An AI system that autonomously generates and optimizes trading strategies using unsupervised learning and reinforcement. It continuously evolves by analyzing market data and adapting to new conditions without human intervention.

## Strategy
Develop a neural network capable of unsupervised pattern recognition from market data. Implement reinforcement learning to test and optimize generated strategies in simulated environments. Deploy the system to trade live, collect performance data, and refine the strategy generation algorithm based on outcomes. Integrate feedback loops for continuous self-improvement.

## Execution Output
SUMMARY: Developed the foundational architecture for the Autonomous StrategyXformer system. Created a modular, production-ready system with robust error handling, logging, and Firebase integration for state management. Implemented core components including data collection, feature engineering, unsupervised learning, and reinforcement learning modules, all designed for continuous autonomous operation.

OUTPUT:

### FILE: requirements.txt
```
firebase-admin>=6.5.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
ccxt>=4.0.0
TA-Lib>=0.4.26
schedule>=1.2.0
joblib>=1.3.0
python-dotenv>=1.0.0
```

### FILE: config.py
```
"""
Configuration module for Autonomous StrategyXformer
Centralized configuration with environment variable fallbacks
"""
import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    
    def __post_init__(self):
        """Validate Firebase credentials on initialization"""
        if not all([self.project_id, self.private_key_id, 
                   self.private_key, self.client_email]):
            raise ValueError("Missing Firebase configuration parameters")
        
        # Fix escaped newlines in private key from environment variables
        if '\\n' in self.private_key:
            self.private_key = self.private_key.replace('\\n', '\n')

@dataclass
class ExchangeConfig:
    """Exchange API configuration"""
    exchange_id: str = "binance"
    symbols: List[str] = None
    timeframe: str = "1h"
    rate_limit: bool = True
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC/USDT", "ETH/USDT"]

@dataclass
class ModelConfig:
    """Machine learning model configuration"""
    n_clusters: int = 8
    state_dim: int = 50
    action_dim: int = 3  # Buy, Sell, Hold
    hidden_dim: int = 128
    gamma: float = 0.99
    learning_rate: float = 0.001
    
    def validate(self):
        if self.n_clusters <= 0:
            raise ValueError("n_clusters must be positive")
        if self.gamma <= 0 or self.gamma >= 1:
            raise ValueError("gamma must be between 0 and 1")

class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Firebase Configuration
        self.firebase = FirebaseConfig(
            project_id=os.getenv('FIREBASE_PROJECT_ID', ''),
            private_key_id=os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
            private_key=os.getenv('FIREBASE_PRIVATE_KEY', ''),
            client_email=os.getenv('FIREBASE_CLIENT_EMAIL', '')
        )
        
        # Exchange Configuration
        self.exchange = ExchangeConfig()
        
        # Model Configuration
        self.model = ModelConfig()
        self.model.validate()
        
        # System Configuration
        self.data_collection_interval: int = 3600  # 1 hour in seconds
        self.retraining_interval: int = 86400  # 24 hours in seconds
        self.max_retries: int = 3
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        
        # Feature Engineering
        self.feature_windows = [5, 10, 20, 50, 100]
        self.technical_indicators = [
            'rsi', 'macd', 'bb_upper', 'bb_middle', 'bb_lower',
            'atr', 'obv', 'ema_12', 'ema_26'
        ]
        
        # Database paths
        self.firestore_collections = {
            'market_data': 'market_data',
            'features': 'features',
            'clusters': 'clusters',
            'strategies': 'strategies',
            'performance': 'performance',
            'system_logs': 'system_logs'
        }
    
    def validate_config(self) -> bool:
        """Validate all configuration parameters"""
        try:
            self.model.validate()
            if not self.firebase.project_id:
                raise ValueError("Firebase project ID is required")
            if self.data_collection_interval <= 0:
                raise ValueError("Data collection interval must be positive")
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")

# Global configuration instance
config = Config()
```

### FILE: logger.py
```
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