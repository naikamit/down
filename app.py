# app.py - Main Flask application with webhook endpoint and dashboard
from flask import Flask, request, jsonify, render_template
import logging
import os
import json
import traceback
from datetime import datetime
import pytz

# Use direct API implementation
from tasty_api import TastyTradeAPI as TastyClient
from binary_search import BinarySearch
from trading import TradingLogic
from logger import api_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize these variables at global scope
tasty_client = None
binary_search = None
trading_logic = None
initialization_error = None

# Try to initialize TastyTrade client and trading logic
try:
    tasty_client = TastyClient()
    binary_search = BinarySearch(tasty_client)
    trading_logic = TradingLogic(tasty_client, binary_search)
    logger.info("Successfully initialized TastyTrade client and trading logic")
except Exception as e:
    initialization_error = str(e)
    logger.error(f"Error initializing TastyTrade client: {str(e)}")
    logger.error(traceback.format_exc())
    # We'll continue initialization, but the app won't work until the client is fixed

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint to receive trading signals"""
    try:
        # Log the incoming request
        request_id = api_logger.log_request('/webhook', 'POST', data=request.json)
        
        # Check if trading_logic is initialized
        if trading_logic is None:
            error_msg = "Trading logic not initialized. Check server logs for details."
            if initialization_error:
                error_msg += f" Error: {initialization_error}"
            api_logger.log_error(request_id, error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # Parse the signal
        data = request.json
        signal = data.get('signal')
        
        if not signal:
            error_msg = "No signal provided in request"
            api_logger.log_error(request_id, error_msg)
            return jsonify({"status": "error", "message": error_msg}), 400
            
        # Handle the signal
        if signal.lower() == 'long':
            trading_logic.handle_long_signal()
            response = {"status": "success", "message": "Long signal processed successfully"}
        elif signal.lower() == 'short':
            trading_logic.handle_short_signal()
            response = {"status": "success", "message": "Short signal processed successfully"}
        else:
            error_msg = f"Unknown signal: {signal}"
            api_logger.log_error(request_id, error_msg)
            return jsonify({"status": "error", "message": error_msg}), 400
            
        # Log the response
        api_logger.log_response(request_id, response)
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Log the error if we have a request ID
        if 'request_id' in locals():
            api_logger.log_error(request_id, error_msg)
            
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/')
def dashboard():
    """Dashboard to display API logs"""
    # Include initialization status in the template
    init_status = {
        "tasty_client": tasty_client is not None,
        "binary_search": binary_search is not None,
        "trading_logic": trading_logic is not None,
        "error": initialization_error
    }
    return render_template('dashboard.html', init_status=init_status)

@app.route('/api/logs')
def get_logs():
    """API endpoint to get all logs"""
    logs = api_logger.get_logs()
    return jsonify(logs)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    if tasty_client is None:
        return jsonify({"status": "error", "message": "TastyTrade client not initialized"}), 500
        
    try:
        # Try to get available cash as a simple test
        available_cash = tasty_client.get_available_cash()
        return jsonify({
            "status": "ok", 
            "message": "API connection successful",
            "available_cash": available_cash
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
