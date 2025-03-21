import json
import time
from datetime import datetime, timedelta

def format_timestamp(timestamp):
    """
    Format a timestamp for display
    """
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def parse_timestamp(timestamp_str):
    """
    Parse a timestamp string into a datetime object
    """
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

def calculate_date_range(days=30):
    """
    Calculate a date range from now to N days ago
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def measure_execution_time(func):
    """
    Decorator to measure the execution time of a function
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Function {func.__name__} executed in {execution_time:.2f} ms")
        return result, execution_time
    return wrapper

def serialize_to_json(obj):
    """
    Serialize an object to JSON, handling datetime objects
    """
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    return json.dumps(obj, default=json_serial)

def deserialize_from_json(json_str):
    """
    Deserialize a JSON string
    """
    return json.loads(json_str)
