# tasty_api.py - Direct TastyTrade API client without SDK dependency
import logging
import os
import requests
import json
import time

logger = logging.getLogger(__name__)

class TastyTradeAPI:
    """Direct implementation of TastyTrade API without the SDK dependency"""
    
    def __init__(self):
        """Initialize the API client with credentials from environment variables"""
        self.login_email = os.environ.get('TASTYTRADE_LOGIN')
        self.password = os.environ.get('TASTYTRADE_PASSWORD')
        self.base_url = f"https://{os.environ.get('API_BASE_URL', 'api.tastytrade.com')}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'tastytrade-webhook-service/1.0',
            'Content-Type': 'application/json'
        })
        self.account_number = None
        self.session_token = None
        self._login()
    
    def _login(self):
        """Authenticate with TastyTrade API and get session token"""
        try:
            logger.info(f"Logging in with email: {self.login_email}")
            
            response = self.session.post(
                f"{self.base_url}/sessions",
                json={
                    "login": self.login_email,
                    "password": self.password
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data['data']['session-token']
            self.session.headers.update({
                'Authorization': self.session_token
            })
            
            # Get account number
            accounts_response = self.session.get(f"{self.base_url}/customers/me/accounts")
            accounts_response.raise_for_status()
            
            accounts = accounts_response.json()['data']['items']
            if not accounts:
                raise ValueError("No accounts found for this user")
            
            self.account_number = accounts[0]['account']['account-number']
            logger.info(f"Logged in successfully, using account {self.account_number}")
            
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            raise
    
    def logout(self):
        """End the session"""
        if self.session_token:
            try:
                self.session.delete(f"{self.base_url}/sessions")
                self.session_token = None
                logger.info("Logged out successfully")
            except Exception as e:
                logger.error(f"Error logging out: {str(e)}")
    
    def get_account_balance(self):
        """Get account balance information"""
        response = self.session.get(f"{self.base_url}/accounts/{self.account_number}/balances")
        response.raise_for_status()
        return response.json()['data']
    
    def get_positions(self):
        """Get current positions"""
        response = self.session.get(f"{self.base_url}/accounts/{self.account_number}/positions")
        response.raise_for_status()
        return response.json()['data']['items']
    
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
            response = self.session.post(
                f"{self.base_url}/accounts/{self.account_number}/orders",
                json=order_data
            )
            response.raise_for_status()
            return response.json()
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
            response = self.session.post(
                f"{self.base_url}/accounts/{self.account_number}/orders",
                json=order_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise
            
    def get_available_cash(self):
        """Get available cash in the account"""
        balance = self.get_account_balance()
        return float(balance['cash-available-to-withdraw'])
