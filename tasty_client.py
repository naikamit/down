# tasty_client.py - TastyTrade API client wrapper
import logging
import os
from tastytrade_sdk import Tastytrade

logger = logging.getLogger(__name__)

class TastyClient:
    def __init__(self):
        """Initialize TastyTrade client with environment credentials"""
        self.login_email = os.environ.get('TASTYTRADE_LOGIN')
        self.password = os.environ.get('TASTYTRADE_PASSWORD')
        api_base_url = os.environ.get('API_BASE_URL', 'api.tastytrade.com')
        
        if not self.login_email or not self.password:
            raise ValueError("TASTYTRADE_LOGIN and TASTYTRADE_PASSWORD must be set in environment variables")
        
        self.client = Tastytrade(api_base_url=api_base_url)
        self.account_number = None
        self._login()
    
    def _login(self):
        """Login to TastyTrade API"""
        try:
            logger.info(f"Logging in with email: {self.login_email}")
            self.client.login(self.login_email, self.password)
            
            # Get the customer account number
            response = self.client.api.get('/customers/me/accounts')
            accounts = response['data']['items']
            if not accounts:
                raise ValueError("No accounts found for this user")
            
            # Use the first account
            self.account_number = accounts[0]['account']['account-number']
            logger.info(f"Logged in successfully, using account {self.account_number}")
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            raise
    
    def get_account_balance(self):
        """Get account balance information"""
        response = self.client.api.get(f'/accounts/{self.account_number}/balances')
        return response['data']
    
    def get_positions(self):
        """Get current positions"""
        response = self.client.api.get(f'/accounts/{self.account_number}/positions')
        return response['data']['items']
    
    def buy_shares(self, symbol, quantity):
        """
        Buy shares of a given symbol
        
        Args:
            symbol: Stock symbol to buy
            quantity: Number of shares to buy
            
        Returns:
            Order response
        """
        order_data = {
            "time-in-force": "Day",
            "order-type": "Market",
            "legs": [
                {
                    "instrument-type": "Equity",
                    "symbol": symbol,
                    "quantity": quantity,
                    "action": "Buy to Open"
                }
            ]
        }
        
        try:
            logger.info(f"Buying {quantity} shares of {symbol}")
            response = self.client.api.post(
                f'/accounts/{self.account_number}/orders',
                data=order_data
            )
            return response
        except Exception as e:
            logger.error(f"Error buying shares: {str(e)}")
            raise
    
    def close_position(self, symbol):
        """
        Close a position for a given symbol
        
        Args:
            symbol: Stock symbol to close
            
        Returns:
            Order response or None if no position exists
        """
        # Get current positions to find the one to close
        positions = self.get_positions()
        position = next((p for p in positions if p['symbol'] == symbol), None)
        
        if not position:
            logger.info(f"No position found for {symbol}, nothing to close")
            return None
        
        quantity = abs(float(position['quantity']))
        if quantity <= 0:
            logger.info(f"Position for {symbol} has zero quantity, nothing to close")
            return None
            
        # Determine if we need to buy or sell to close
        action = "Sell to Close" if position['quantity-direction'] == "Long" else "Buy to Close"
        
        order_data = {
            "time-in-force": "Day",
            "order-type": "Market",
            "legs": [
                {
                    "instrument-type": "Equity",
                    "symbol": symbol,
                    "quantity": quantity,
                    "action": action
                }
            ]
        }
        
        try:
            logger.info(f"Closing position for {symbol} with {action} for {quantity} shares")
            response = self.client.api.post(
                f'/accounts/{self.account_number}/orders',
                data=order_data
            )
            return response
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise
            
    def get_available_cash(self):
        """Get available cash in the account"""
        balance = self.get_account_balance()
        return float(balance['cash-available-to-withdraw'])
