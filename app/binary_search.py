# app/binary_search.py
import logging
import time

logger = logging.getLogger(__name__)

def binary_search_shares(buy_function, max_shares, symbol, available_cash):
    """
    Use binary search to find the maximum number of whole shares that can be purchased
    
    Args:
        buy_function: Function to call to attempt to buy shares
        max_shares: Maximum number of shares to attempt
        symbol: The stock symbol to buy
        available_cash: Available cash for the purchase
        
    Returns:
        Dictionary with the result of the purchase
    """
    logger.info(f"Starting binary search for {symbol} with max shares {max_shares} and available cash ${available_cash}")
    
    # Start with the configured maximum shares
    low = 1
    high = max_shares
    
    # Track the last successful purchase
    last_successful = None
    attempts = 0
    max_attempts = 10  # Limit number of attempts to prevent excessive API calls
    
    while low <= high and attempts < max_attempts:
        attempts += 1
        mid = (low + high) // 1  # Ensure we're dealing with whole shares
        
        # Don't attempt to buy 0 shares
        if mid == 0:
            break
            
        logger.info(f"Attempt {attempts}: Trying to buy {mid} shares of {symbol}")
        
        # Attempt to buy shares
        result = buy_function(symbol, mid)
        
        if result.get('success'):
            logger.info(f"Successfully bought {mid} shares of {symbol}")
            
            # Store the last successful purchase
            last_successful = result
            
            # If we're at the top of our range, we're done
            if mid == high:
                break
                
            # Try to buy more shares
            low = mid + 1
        else:
            logger.info(f"Failed to buy {mid} shares of {symbol}")
            
            # If we're at the bottom of our range, we can't buy any
            if mid == low:
                break
                
            # Try to buy fewer shares
            high = mid - 1
        
        # Small delay to avoid hitting API rate limits
        time.sleep(0.5)
    
    # Return the last successful purchase or a failure message
    if last_successful:
        return last_successful
    else:
        logger.warning(f"Could not buy any shares of {symbol} after {attempts} attempts")
        return {"success": False, "message": f"Could not buy any shares after {attempts} attempts"}
