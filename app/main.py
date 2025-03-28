# app/main.py
from flask import Flask, request, render_template, jsonify
import os
import logging
from datetime import datetime, timedelta
import pytz

from app.trading import process_long_signal, process_short_signal, close_positions
from app.dashboard import add_event, get_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
last_successful_trade_time = None
cooldown_hours = int(os.environ.get('COOLDOWN_HOURS', 12))

@app.route('/')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/events')
def api_events():
    """API endpoint to get events for the dashboard"""
    return jsonify(get_events())

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from TradingView"""
    try:
        # Parse the incoming JSON data
        data = request.json
        
        # Log the incoming webhook
        logger.info(f"Received webhook: {data}")
        
        # Add event to dashboard
        add_event('incoming', 'webhook', data)
        
        # Check if we're in cooldown period
        global last_successful_trade_time
        if last_successful_trade_time:
            cooldown_end = last_successful_trade_time + timedelta(hours=cooldown_hours)
            now = datetime.now(pytz.UTC)
            
            if now < cooldown_end:
                logger.info(f"In cooldown period until {cooldown_end.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                # During cooldown, close all positions
                mstu_result = close_positions('MSTU')
                mstz_result = close_positions('MSTZ')
                return jsonify({
                    "status": "success",
                    "message": "In cooldown period - closed all positions",
                    "result": {
                        "mstu_close": mstu_result,
                        "mstz_close": mstz_result
                    }
                })
        
        # Process the signal
        signal = data.get('signal', '').lower()
        if signal == 'long':
            result = process_long_signal()
            return jsonify({
                "status": "success",
                "message": "Processed long signal",
                "result": result
            })
        elif signal == 'short':
            result = process_short_signal()
            return jsonify({
                "status": "success",
                "message": "Processed short signal",
                "result": result
            })
        else:
            add_event('error', 'webhook', {"error": "Invalid signal", "data": data})
            return jsonify({
                "status": "error",
                "message": "Invalid signal"
            }), 400
            
    except Exception as e:
        logger.exception("Error processing webhook")
        add_event('error', 'webhook', {"error": str(e)})
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def set_successful_trade():
    """Mark a successful trade and start the cooldown period"""
    global last_successful_trade_time
    last_successful_trade_time = datetime.now(pytz.UTC)
    logger.info(f"Successful trade at {last_successful_trade_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info(f"Cooldown period started for {cooldown_hours} hours")
    return last_successful_trade_time

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
