# app/dashboard.py
from datetime import datetime
import pytz
import json

# Store events in memory (since we don't want to use a DB)
events = []
max_events = 1000  # Limit the number of events to prevent memory issues

def add_event(direction, event_type, data):
    """
    Add an event to the history
    
    Args:
        direction: 'incoming', 'outgoing', or 'error'
        event_type: Type of event (webhook, api_call, etc.)
        data: The data associated with the event
    """
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    
    event = {
        'timestamp': timestamp,
        'direction': direction,
        'type': event_type,
        'data': data
    }
    
    # Add to the beginning of the list for reverse chronological order
    events.insert(0, event)
    
    # Limit the size of the events list
    if len(events) > max_events:
        events.pop()
    
    return event

def get_events():
    """
    Get all events for the dashboard
    
    Returns:
        List of events
    """
    return events
