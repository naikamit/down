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
        """Check if we're in the lockout period after a successful buy"""
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
        
    def _positions_exist(self):
        """Check if any positions exist in the account"""
        positions = self.tasty_client.get_positions()
        return len(positions) > 0
        
    def _close_all_positions(self):
        """Close all positions in the account"""
        logger.info("Closing all positions")
        positions = self.tasty_client.get_positions()
        
        for position in positions:
            symbol = position['symbol']
            self.tasty_client.close_position(symbol)
            logger.info(f"Closed position for {symbol}")
            
    def handle_long_signal(self):
        """
        Handle a long signal
        
        If in lockout period: close all positions
        If positions exist: buy max MSTU, wait 1s, close MSTZ
        If only cash: buy MSTU with 50% of available cash
        """
        logger.info("Handling long signal")
        
        # If in lockout period, close all positions and return
        if self._is_in_lockout_period():
            logger.info("In lockout period, closing all positions")
            self._close_all_positions()
            return
            
        if self._positions_exist():
            logger.info("Positions exist, buying max MSTU and closing MSTZ")
            # Buy as many MSTU shares as possible with all available cash
            shares_bought = self.binary_search.find_max_buyable_shares(self.long_symbol)
            
            if shares_bought > 0:
                logger.info(f"Successfully bought {shares_bought} shares of {self.long_symbol}")
                self.last_successful_buy = datetime.now()
                
                # Pause 1 second
                time.sleep(1)
                
                # Close all MSTZ positions
                self.tasty_client.close_position(self.short_symbol)
            else:
                logger.warning(f"Failed to buy any shares of {self.long_symbol}")
        else:
            logger.info("No positions exist, buying MSTU with 50% of available cash")
            # Only cash exists, buy MSTU with 50% of available cash
            shares_bought = self.binary_search.find_max_buyable_shares(self.long_symbol, max_cash_percentage=0.5)
            
            if shares_bought > 0:
                logger.info(f"Successfully bought {shares_bought} shares of {self.long_symbol} with 50% of available cash")
                self.last_successful_buy = datetime.now()
            else:
                logger.warning(f"Failed to buy any shares of {self.long_symbol}")
                
    def handle_short_signal(self):
        """
        Handle a short signal
        
        If in lockout period: close all positions
        If positions exist: buy max MSTZ, wait 1s, close MSTU
        If only cash: buy MSTZ with 50% of available cash
        """
        logger.info("Handling short signal")
        
        # If in lockout period, close all positions and return
        if self._is_in_lockout_period():
            logger.info("In lockout period, closing all positions")
            self._close_all_positions()
            return
            
        if self._positions_exist():
            logger.info("Positions exist, buying max MSTZ and closing MSTU")
            # Buy as many MSTZ shares as possible with all available cash
            shares_bought = self.binary_search.find_max_buyable_shares(self.short_symbol)
            
            if shares_bought > 0:
                logger.info(f"Successfully bought {shares_bought} shares of {self.short_symbol}")
                self.last_successful_buy = datetime.now()
                
                # Pause 1 second
                time.sleep(1)
                
                # Close all MSTU positions
                self.tasty_client.close_position(self.long_symbol)
            else:
                logger.warning(f"Failed to buy any shares of {self.short_symbol}")
        else:
            logger.info("No positions exist, buying MSTZ with 50% of available cash")
            # Only cash exists, buy MSTZ with 50% of available cash
            shares_bought = self.binary_search.find_max_buyable_shares(self.short_symbol, max_cash_percentage=0.5)
            
            if shares_bought > 0:
                logger.info(f"Successfully bought {shares_bought} shares of {self.short_symbol} with 50% of available cash")
                self.last_successful_buy = datetime.now()
            else:
                logger.warning(f"Failed to buy any shares of {self.short_symbol}")
