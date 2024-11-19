from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta
from api_clients.bitunix_api import ApiBitunix
from storage.storage_manager import StorageManager

@dataclass
class CollectorConfig:
    symbols: List[str]
    intervals: List[str]
    csv_enabled: bool = False
    retry_attempts: int = 3
    batch_size: int = 1000

class BaseDataCollector:
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.setup_logging()
    
    def setup_logging(self):
        raise NotImplementedError
    
    def collect_data(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        raise NotImplementedError

class BitunixDataCollector(BaseDataCollector):
    def __init__(self, config: CollectorConfig):
        super().__init__(config)

        
        self.api_client = ApiBitunix()
        self.storage_manager = StorageManager()
    
    def collect_data(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        try:
            return self.api_client.get_kline_data(symbol, interval)
        except Exception as e:
            self.logger.error(f"Failed to collect data: {e}")
            return None

    @property
    def name(self) -> str:
        return "BitunixCollector"

    def process_data(self, new_data: pd.DataFrame, existing_data: Optional[pd.DataFrame]) -> pd.DataFrame:
        # Data processing logic
        pass