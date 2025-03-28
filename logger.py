# logger.py - Custom logger for tracking API calls
import logging
import json
from datetime import datetime
import pytz
from collections import deque
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a custom logger
logger = logging.getLogger('api_logger')

class ApiLogger:
    """Custom logger for tracking API requests and responses"""
    
    def __init__(self, max_logs=1000):
        """
        Initialize API logger
        
        Args:
            max_logs: Maximum number of logs to store in memory
        """
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()
        
    def log_request(self, endpoint, method, data=None, params=None):
        """
        Log an API request
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            params: Request parameters
            
        Returns:
            Request ID
        """
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        log_entry = {
            'id': len(self.logs) + 1,
            'timestamp': timestamp,
            'type': 'request',
            'endpoint': endpoint,
            'method': method,
            'data': data,
            'params': params,
            'status': 'pending'
        }
        
        with self.lock:
            self.logs.append(log_entry)
            
        logger.info(f"API Request: {method} {endpoint}")
        return log_entry['id']
        
    def log_response(self, request_id, response, status='success'):
        """
        Log an API response
        
        Args:
            request_id: Request ID
            response: Response data
            status: Response status
        """
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        log_entry = {
            'id': request_id,
            'timestamp': timestamp,
            'type': 'response',
            'response': response,
            'status': status
        }
        
        with self.lock:
            # Find the corresponding request and update its status
            for entry in self.logs:
                if entry.get('id') == request_id and entry.get('type') == 'request':
                    entry['status'] = status
                    break
            
            # Add the response log
            self.logs.append(log_entry)
                    
        logger.info(f"API Response: ID {request_id}, Status: {status}")
        
    def log_error(self, request_id, error):
        """
        Log an API error
        
        Args:
            request_id: Request ID
            error: Error message
        """
        self.log_response(request_id, {'error': str(error)}, status='error')
        logger.error(f"API Error: ID {request_id}, Error: {str(error)}")
        
    def get_logs(self):
        """Get all logs"""
        with self.lock:
            return list(self.logs)

# Create a singleton instance
api_logger = ApiLogger()
