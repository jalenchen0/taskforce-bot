from datetime import datetime, timedelta, timezone
import re

def validate_time_format(time_str):
    return re.match(r'^\d{2}:\d{2}$', time_str) is not None

def validate_date_format(date_str):
    return re.match(r'^\d{4}-\d{2}-\d{2}$', date_str) is not None

def format_remaining_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def create_progress_bar(progress, bars=10):
    filled = int(bars * progress)
    empty = bars - filled
    return "█" * filled + "░" * empty

def get_utc_timestamps():
    now = datetime.now(timezone.utc)
    one_min_ago = now - timedelta(minutes=1)
    return (
        one_min_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
        now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
