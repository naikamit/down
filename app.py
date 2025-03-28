# app.py - Main Flask application with webhook endpoint and dashboard
from flask import Flask, request, jsonify, render_template
import logging
import os
import json
import traceback
from datetime import datetime
import pytz
# Update in app.py
from tasty_api import TastyTradeAPI  # Instead of TastyClient

# Update in binary_search.py and trading.py
# Replace tasty_client with tasty_api and update method calls if needed

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

# Initialize TastyTrade client and trading logic
try:
    tasty_client = TastyClient()
    binary_search = BinarySearch(tasty_client)
    trading_logic = TradingLogic(tasty_client, binary_search)
    logger.info("Successfully initialized TastyTrade client and trading logic")
except Exception as e:
    logger.error(f"Error initializing TastyTrade client: {str(e)}")
    logger.error(traceback.format_exc())
    # We'll continue initialization, but the app won't work until the client is fixed

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint to receive trading signals"""
    try:
        # Log the incoming request
        request_id = api_logger.log_request('/webhook', 'POST', data=request.json)
        
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
    return render_template('dashboard.html')

@app.route('/api/logs')
def get_logs():
    """API endpoint to get all logs"""
    logs = api_logger.get_logs()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
