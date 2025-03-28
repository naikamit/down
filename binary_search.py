# binary_search.py - Binary search implementation for maximizing share purchases
import logging
import os
import time

logger = logging.getLogger(__name__)

class BinarySearch:
    def __init__(self, tasty_client):
        """
        Initialize binary search with TastyTrade client
        
        Args:
            tasty_client: Initialized TastyClient instance
        """
        self.tasty_client = tasty_client
        self.initial_max_shares = int(os.environ.get('INITIAL_MAX_SHARES', '5000'))
        
    def find_max_buyable_shares(self, symbol, max_cash_percentage=1.0):
        """
        Find maximum number of shares that can be bought using binary search
        
        Args:
            symbol: Stock symbol to buy
            max_cash_percentage: Maximum percentage of available cash to use (0.0-1.0)
            
        Returns:
            Maximum number of whole shares that can be bought
        """
        available_cash = self.tasty_client.get_available_cash()
        max_cash = available_cash * max_cash_percentage
        
        logger.info(f"Starting binary search for {symbol} with {max_cash:.2f} available cash ({max_cash_percentage*100}% of {available_cash:.2f})")
        
        if max_cash <= 0:
            logger.warning("No cash available for buying shares")
            return 0
            
        low = 1  # Minimum 1 share
        high = self.initial_max_shares
        best_quantity = 0
        
        while low <= high:
            mid = (low + high) // 2
            logger.info(f"Binary search: Trying to buy {mid} shares of {symbol}")
            
            try:
                # Try to buy shares
                response = self.tasty_client.buy_shares(symbol, mid)
                
                # Check if order was accepted
                order_status = response.get('data', {}).get('order', {}).get('status')
                
                if order_status in ['Filled', 'Live', 'Routed']:
                    logger.info(f"Binary search: Successfully bought {mid} shares of {symbol}")
                    best_quantity = mid
                    low = mid + 1  # Try to buy more
                else:
                    logger.warning(f"Binary search: Order not successful, status: {order_status}")
                    high = mid - 1  # Try to buy less
                    
            except Exception as e:
                logger.error(f"Binary search: Error while trying to buy {mid} shares: {str(e)}")
                high = mid - 1  # Try to buy less
                
            # Add a small delay between API calls to avoid rate limiting
            time.sleep(0.5)
            
        return best_quantity
