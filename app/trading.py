# app/trading.py
import os
import logging
import time
from datetime import datetime, timedelta
import pytz
from tastytrade_sdk import Tastytrade
from binary_search import binary_search_shares
from dashboard import add_event

logger = logging.getLogger(__name__)

# Initialize the Tastytrade client
api_base_url = os.environ.get('API_BASE_URL', 'api.tastytrade.com')
tastytrade = None

# Cache for authentication token
auth_expiry = None

def ensure_authenticated():
    """Ensure we're authenticated with the tastytrade API"""
    global auth_expiry, tastytrade
    
    # If we have a valid token, use it
    if auth_expiry and datetime.now(pytz.UTC) < auth_expiry:
        return True
    
    # Otherwise, authenticate
    logger.info("Authenticating with tastytrade API")
    try:
        login = os.environ.get('TASTYTRADE_LOGIN')
        password = os.environ.get('TASTYTRADE_PASSWORD')
        
        if not login or not password:
            raise ValueError("TASTYTRADE_LOGIN and TASTYTRADE_PASSWORD must be set")
        
        # Initialize new client if needed
        if tastytrade is None:
            tastytrade = Tastytrade(api_base_url=api_base_url)
            
        tastytrade.login(login, password)
        
        # Token is valid for 24 hours, but we'll refresh after 23 hours to be safe
        auth_expiry = datetime.now(pytz.UTC) + timedelta(hours=23)
        
        logger.info("Successfully authenticated with tastytrade API")
        add_event('outgoing', 'api_auth', {"status": "success"})
        return True
    except Exception as e:
        logger.exception("Failed to authenticate with tastytrade API")
        add_event('error', 'api_auth', {"error": str(e)})
        return False

def get_account_balances():
    """Get account balances"""
    if not ensure_authenticated():
        return {"error": "Authentication failed"}
    
    try:
        logger.info("Getting account balances")
        
        # Make the API call to get account balances
        response = tastytrade.api.get('/accounts/balances')
        add_event('outgoing', 'api_call', {
            "endpoint": "/accounts/balances",
            "method": "GET",
            "response": response
        })
        
        # Extract the cash balance
        items = response.get('data', {}).get('items', [])
        if not items:
            return {"error": "No accounts found"}
            
        cash_balance = items[0].get('cash-balance', 0)
        
        logger.info(f"Cash balance: {cash_balance}")
        return {"cash_balance": float(cash_balance)}
    except Exception as e:
        logger.exception("Error getting account balances")
        add_event('error', 'api_call', {
            "endpoint": "/accounts/balances",
            "method": "GET",
            "error": str(e)
        })
        return {"error": str(e)}

def get_account_positions():
    """Get account positions"""
    if not ensure_authenticated():
        return {"error": "Authentication failed"}
    
    try:
        logger.info("Getting account positions")
        
        # Make the API call to get positions
        response = tastytrade.api.get('/accounts/positions')
        add_event('outgoing', 'api_call', {
            "endpoint": "/accounts/positions",
            "method": "GET",
            "response": response
        })
        
        # Extract the positions
        positions = response.get('data', {}).get('items', [])
        
        # Filter for MSTU and MSTZ positions
        mstu_positions = [p for p in positions if p.get('symbol') == 'MSTU']
        mstz_positions = [p for p in positions if p.get('symbol') == 'MSTZ']
        
        logger.info(f"MSTU positions: {len(mstu_positions)}")
        logger.info(f"MSTZ positions: {len(mstz_positions)}")
        
        return {
            "positions": positions,
            "mstu_positions": mstu_positions,
            "mstz_positions": mstz_positions
        }
    except Exception as e:
        logger.exception("Error getting account positions")
        add_event('error', 'api_call', {
            "endpoint": "/accounts/positions",
            "method": "GET",
            "error": str(e)
        })
        return {"error": str(e)}

def buy_shares(symbol, quantity):
    """
    Buy shares of a stock
    
    Args:
        symbol: The stock symbol to buy
        quantity: The number of shares to buy
        
    Returns:
        Dictionary with the result of the purchase
    """
    if not ensure_authenticated():
        return {"success": False, "error": "Authentication failed"}
    
    try:
        logger.info(f"Buying {quantity} shares of {symbol}")
        
        # Get the current account
        accounts_response = tastytrade.api.get('/accounts')
        add_event('outgoing', 'api_call', {
            "endpoint": "/accounts",
            "method": "GET",
            "response": accounts_response
        })
        
        items = accounts_response.get('data', {}).get('items', [])
        if not items:
            return {"success": False, "error": "No accounts found"}
            
        account_number = items[0].get('account-number')
        
        # Prepare the order data
        order_data = {
            "account-number": account_number,
            "source": "API",
            "order-type": "Market",
            "price-effect": "Debit",
            "time-in-force": "Day",
            "legs": [
                {
                    "instrument-type": "Equity",
                    "symbol": symbol,
                    "quantity": quantity,
                    "side": "Buy"
                }
            ]
        }
        
        # Make the API call to place the order
        response = tastytrade.api.post('/accounts/orders', data=order_data)
        add_event('outgoing', 'api_call', {
            "endpoint": "/accounts/orders",
            "method": "POST",
            "request": order_data,
            "response": response
        })
        
        # Check if the order was successful
        order = response.get('data', {}).get('order', {})
        if order.get('status') == 'Received':
            logger.info(f"Successfully bought {quantity} shares of {symbol}")
            
            # Mark a successful trade
            from main import set_successful_trade
            set_successful_trade()
            
            return {
                "success": True,
                "order_id": order.get('id'),
                "status": order.get('status'),
                "quantity": quantity,
                "symbol": symbol
            }
        else:
            logger.warning(f"Failed to buy {quantity} shares of {symbol}")
            return {
                "success": False,
                "response": response,
                "message": "Order not received"
            }
    except Exception as e:
        logger.exception(f"Error buying {quantity} shares of {symbol}")
        add_event('error', 'api_call', {
            "endpoint": "/accounts/orders",
            "method": "POST",
            "error": str(e)
        })
        return {"success": False, "error": str(e)}

def close_positions(symbol):
    """
    Close all positions for a symbol
    
    Args:
        symbol: The stock symbol to close positions for
        
    Returns:
        Dictionary with the result of the operation
    """
    if not ensure_authenticated():
        return {"success": False, "error": "Authentication failed"}
    
    try:
        # Get positions
        positions_result = get_account_positions()
        
        if 'error' in positions_result:
            return {"success": False, "error": positions_result['error']}
        
        # Filter positions for the specified symbol
        if symbol == 'MSTU':
            symbol_positions = positions_result['mstu_positions']
        elif symbol == 'MSTZ':
            symbol_positions = positions_result['mstz_positions']
        else:
            symbol_positions = [p for p in positions_result['positions'] if p.get('symbol') == symbol]
        
        if not symbol_positions:
            logger.info(f"No {symbol} positions to close")
            return {"success": True, "message": f"No {symbol} positions to close"}
        
        # Get the current account
        accounts_response = tastytrade.api.get('/accounts')
        add_event('outgoing', 'api_call', {
            "endpoint": "/accounts",
            "method": "GET",
            "response": accounts_response
        })
        
        items = accounts_response.get('data', {}).get('items', [])
        if not items:
            return {"success": False, "error": "No accounts found"}
            
        account_number = items[0].get('account-number')
        
        # Close each position
        results = []
        for position in symbol_positions:
            quantity = abs(float(position.get('quantity', 0)))
            
            if quantity <= 0:
                logger.warning(f"Invalid quantity {quantity} for position {position}")
                continue
                
            # Prepare the order data for selling
            order_data = {
                "account-number": account_number,
                "source": "API",
                "order-type": "Market",
                "price-effect": "Credit",
                "time-in-force": "Day",
                "legs": [
                    {
                        "instrument-type": "Equity",
                        "symbol": symbol,
                        "quantity": int(quantity),
                        "side": "Sell"
                    }
                ]
            }
            
            # Make the API call to place the sell order
            response = tastytrade.api.post('/accounts/orders', data=order_data)
            add_event('outgoing', 'api_call', {
                "endpoint": "/accounts/orders",
                "method": "POST",
                "request": order_data,
                "response": response
            })
            
            # Check if the order was successful
            order = response.get('data', {}).get('order', {})
            if order.get('status') == 'Received':
                logger.info(f"Successfully closed {quantity} shares of {symbol}")
                results.append({
                    "success": True,
                    "order_id": order.get('id'),
                    "status": order.get('status'),
                    "quantity": quantity,
                    "symbol": symbol
                })
            else:
                logger.warning(f"Failed to close {quantity} shares of {symbol}")
                results.append({
                    "success": False,
                    "response": response,
                    "message": "Order not received"
                })
        
        return {"success": True, "results": results}
    except Exception as e:
        logger.exception(f"Error closing positions for {symbol}")
        add_event('error', 'api_call', {
            "endpoint": "/accounts/orders",
            "method": "POST",
            "error": str(e)
        })
        return {"success": False, "error": str(e)}

def process_long_signal():
    """Process a long signal"""
    logger.info("Processing long signal")
    
    try:
        # Get account positions and balances
        positions_result = get_account_positions()
        balances_result = get_account_balances()
        
        if 'error' in positions_result or 'error' in balances_result:
            return {
                "success": False,
                "positions_error": positions_result.get('error'),
                "balances_error": balances_result.get('error')
            }
        
        # Check if we have any positions
        has_positions = len(positions_result['positions']) > 0
        cash_balance = balances_result['cash_balance']
        
        # Set up parameters for binary search
        max_shares = int(os.environ.get('MAX_SHARES_ATTEMPT', 5000))
        
        if has_positions:
            logger.info("Positions exist, buying MSTU with full cash balance")
            # Buy as many MSTU shares as possible
            mstu_result = binary_search_shares(buy_shares, max_shares, 'MSTU', cash_balance)
            
            # Pause 1 second
            time.sleep(1)
            
            # Close all MSTZ positions
            mstz_result = close_positions('MSTZ')
            
            return {
                "success": True,
                "has_positions": True,
                "cash_balance": cash_balance,
                "mstu_buy": mstu_result,
                "mstz_close": mstz_result
            }
        else:
            logger.info("No positions exist, buying MSTU with partial cash balance")
            # Buy as many MSTU shares as possible with 50% of cash
            cash_allocation_percent = int(os.environ.get('CASH_ALLOCATION_PERCENT', 50))
            allocated_cash = cash_balance * (cash_allocation_percent / 100.0)
            
            logger.info(f"Cash balance: ${cash_balance}, Allocation: {cash_allocation_percent}%, Allocated: ${allocated_cash}")
            
            # Estimate the maximum number of shares we can buy
            mstu_result = binary_search_shares(buy_shares, max_shares, 'MSTU', allocated_cash)
            
            return {
                "success": True,
                "has_positions": False,
                "cash_balance": cash_balance,
                "allocation_percent": cash_allocation_percent,
                "allocated_cash": allocated_cash,
                "mstu_buy": mstu_result
            }
    except Exception as e:
        logger.exception("Error processing long signal")
        add_event('error', 'process_signal', {"signal": "long", "error": str(e)})
        return {"success": False, "error": str(e)}

def process_short_signal():
    """Process a short signal"""
    logger.info("Processing short signal")
    
    try:
        # Get account positions and balances
        positions_result = get_account_positions()
        balances_result = get_account_balances()
        
        if 'error' in positions_result or 'error' in balances_result:
            return {
                "success": False,
                "positions_error": positions_result.get('error'),
                "balances_error": balances_result.get('error')
            }
        
        # Check if we have any positions
        has_positions = len(positions_result['positions']) > 0
        cash_balance = balances_result['cash_balance']
        
        # Set up parameters for binary search
        max_shares = int(os.environ.get('MAX_SHARES_ATTEMPT', 5000))
        
        if has_positions:
            logger.info("Positions exist, buying MSTZ with full cash balance")
            # Buy as many MSTZ shares as possible
            mstz_result = binary_search_shares(buy_shares, max_shares, 'MSTZ', cash_balance)
            
            # Pause 1 second
            time.sleep(1)
            
            # Close all MSTU positions
            mstu_result = close_positions('MSTU')
            
            return {
                "success": True,
                "has_positions": True,
                "cash_balance": cash_balance,
                "mstz_buy": mstz_result,
                "mstu_close": mstu_result
            }
        else:
            logger.info("No positions exist, buying MSTZ with partial cash balance")
            # Buy as many MSTZ shares as possible with 50% of cash
            cash_allocation_percent = int(os.environ.get('CASH_ALLOCATION_PERCENT', 50))
            allocated_cash = cash_balance * (cash_allocation_percent / 100.0)
            
            logger.info(f"Cash balance: ${cash_balance}, Allocation: {cash_allocation_percent}%, Allocated: ${allocated_cash}")
            
            # Estimate the maximum number of shares we can buy
            mstz_result = binary_search_shares(buy_shares, max_shares, 'MSTZ', allocated_cash)
            
            return {
                "success": True,
                "has_positions": False,
                "cash_balance": cash_balance,
                "allocation_percent": cash_allocation_percent,
                "allocated_cash": allocated_cash,
                "mstz_buy": mstz_result
            }
    except Exception as e:
        logger.exception("Error processing short signal")
        add_event('error', 'process_signal', {"signal": "short", "error": str(e)})
        return {"success": False, "error": str(e)}
