"""
Time Utilities - Handle local timezone for all users
"""

from datetime import datetime
from typing import Optional

def get_local_time() -> datetime:
    """Get current time in user's local timezone"""
    return datetime.now()

def format_local_time(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in user's local timezone"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

def get_local_date() -> str:
    """Get current date in local timezone"""
    return datetime.now().strftime("%Y-%m-%d")

def get_local_time_only() -> str:
    """Get current time only in local timezone"""
    return datetime.now().strftime("%H:%M:%S")

def get_us_market_time() -> str:
    """Get US market time (EST/EDT)"""
    from datetime import timezone, timedelta
    
    utc = timezone.utc
    now_utc = datetime.now(utc)
    month = now_utc.month
    
    # DST check
    if month >= 3 and month <= 10:
        est_offset = timedelta(hours=-4)  # EDT
    else:
        est_offset = timedelta(hours=-5)  # EST
    
    est = timezone(est_offset)
    now_est = now_utc.astimezone(est)
    return now_est.strftime("%H:%M:%S %Z")

def get_timezone_info() -> dict:
    """Get timezone information for display"""
    local = datetime.now()
    return {
        'local_time': local.strftime("%Y-%m-%d %H:%M:%S"),
        'timezone_name': str(local.tzinfo) if hasattr(local, 'tzinfo') else 'Local',
        'utc_offset': local.strftime("%Z"),
        'us_market_time': get_us_market_time()
    }