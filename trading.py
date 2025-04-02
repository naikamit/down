# trading.py - Trading logic for handling signals
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TradingLogic:
    def __init__(self, tasty_client, binary_search):
        """
        Initialize trading logic with TastyTrade client and binary search
        
        Args:
            tasty_client: Initialized TastyClient instance
            binary_search: Initialized BinarySearch instance
        """
        self.tasty_client = tasty_client
        self.binary_search = binary_search
        self.last_successful_buy = None
        self.lockout_hours = 12
        
        # Stock symbols
        self.long_symbol = "MSTU"
        self.short_symbol = "MSTZ"
    
    def _is_in_lockout_period(self):
        """
        Check if we're in the lockout period after a successful buy
        
        Returns:
            bool: True if in lockout period, False otherwise
        """
        if not self.last_successful_buy:
            return False
            
        now = datetime.now()
        lockout_end = self.last_successful_buy + timedelta(hours=self.lockout_hours)
        
        if now < lockout_end:
            remaining = lockout_end - now
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            logger.info(f"In lockout period. {hours} hours and {minutes} minutes remaining")
            return True
            
        return False
    
    def _close_position(self, symbol):
        """
        Close a specific position
        
        Args:
            symbol: Stock symbol to close
        """
        logger.info(f"Closing position for {symbol}")
        self.tasty_client.close_position(symbol)
    
    def _close_all_positions(self):
        """Close both MSTU and MSTZ positions"""
        logger.info("Closing all positions (MSTU and MSTZ)")
        self._close_position(self.long_symbol)
        self._close_position(self.short_symbol)
        
    def handle_long_signal(self):
        """
        Handle a long signal
        
        If in lockout period: close all positions
        Otherwise: buy max MSTU, pause 1s, close MSTZ
        """
        logger.info("Handling long signal")
        
        # If in lockout period, close all positions and return
        if self._is_in_lockout_period():
            logger.info("In lockout period, closing all positions")
            self._close_all_positions()
            return
        
        # Use binary search to buy as many MSTU shares as possible
        shares_bought = self.binary_search.find_max_buyable_shares(self.long_symbol)
        
        # Check if shares were successfully bought
        if shares_bought > 0:
            logger.info(f"Successfully bought {shares_bought} shares of {self.long_symbol}")
            self.last_successful_buy = datetime.now()
            
            # Pause 1 second after buying
            logger.info("Pausing for 1 second")
            time.sleep(1)
            
            # Close all MSTZ positions
            logger.info(f"Closing all {self.short_symbol} positions")
            self._close_position(self.short_symbol)
        else:
            logger.warning(f"Failed to buy any shares of {self.long_symbol}")
                
    def handle_short_signal(self):
        """
        Handle a short signal
        
        If in lockout period: close all positions
        Otherwise: buy max MSTZ, pause 1s, close MSTU
        """
        logger.info("Handling short signal")
        
        # If in lockout period, close all positions and return
        if self._is_in_lockout_period():
            logger.info("In lockout period, closing all positions")
            self._close_all_positions()
            return
            
        # Use binary search to buy as many MSTZ shares as possible
        shares_bought = self.binary_search.find_max_buyable_shares(self.short_symbol)
        
        # Check if shares were successfully bought
        if shares_bought > 0:
            logger.info(f"Successfully bought {shares_bought} shares of {self.short_symbol}")
            self.last_successful_buy = datetime.now()
            
            # Pause 1 second after buying
            logger.info("Pausing for 1 second")
            time.sleep(1)
            
            # Close all MSTU positions
            logger.info(f"Closing all {self.long_symbol} positions")
            self._close_position(self.long_symbol)
        else:
            logger.warning(f"Failed to buy any shares of {self.short_symbol}")
