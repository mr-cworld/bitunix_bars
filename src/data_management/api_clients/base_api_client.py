import requests
import logging
from typing import Optional, Dict, Any
import uuid
import time

logger = logging.getLogger(__name__)

class BaseApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers required by the API"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'nonce': str(uuid.uuid4()),
            'timestamp': str(int(time.time() * 1000))
        }
        
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            # Log exact request details
            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Exact params being sent: {params}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params
            )
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            try:
                data = response.json()
                logger.debug(f"Response data: {data}")
                return data
                
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {response.text}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def fetch_data(self):
        raise NotImplementedError("Subclasses should implement this method")
    
    def process_data(self, data):
        raise NotImplementedError("Subclasses should implement this method")