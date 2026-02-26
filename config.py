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