# app/utils.py
from datetime import datetime
import pytz

def format_timestamp(timestamp=None, timezone='Asia/Kolkata'):
    """
    Format a timestamp in the specified timezone
    
    Args:
        timestamp: The timestamp to format (default: current time)
        timezone: The timezone to use (default: IST)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    tz = pytz.timezone(timezone)
    return timestamp.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S %Z')

def format_money(amount):
    """
    Format a monetary amount
    
    Args:
        amount: The amount to format
        
    Returns:
        Formatted amount string with dollar sign and commas
    """
    return f"${amount:,.2f}"
