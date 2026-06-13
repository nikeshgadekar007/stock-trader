"""
Time Utilities - Handle local timezone for all users
"""

from datetime import datetime, timezone, timedelta
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

def get_hk_time() -> str:
    """Get Hong Kong time (UTC+8)"""
    utc = timezone.utc
    now_utc = datetime.now(utc)
    hk_offset = timedelta(hours=8)
    hk = timezone(hk_offset)
    now_hk = now_utc.astimezone(hk)
    return now_hk.strftime("%Y-%m-%d %H:%M:%S HKT")

def get_hk_market_time() -> str:
    """Get Hong Kong time with US market session info"""
    utc = timezone.utc
    now_utc = datetime.now(utc)
    hk_offset = timedelta(hours=8)
    hk = timezone(hk_offset)
    now_hk = now_utc.astimezone(hk)
    
    # Also get US time
    est_offset = timedelta(hours=-5)
    est = timezone(est_offset)
    now_est = now_utc.astimezone(est)
    
    hour = now_est.hour
    
    # US market sessions in HK time
    if 21 <= hour or hour < 4:
        session = "US PRE-MARKET"
    elif 4 <= hour < 9:
        session = "US AFTER HOURS"
    elif 9 <= hour < 16:
        session = "US MARKET OPEN"
    else:
        session = "US MARKET CLOSED"
    
    return f"{now_hk.strftime('%H:%M:%S')} HK | {session}"

def get_timezone_info() -> dict:
    """Get timezone information for display"""
    local = datetime.now()
    return {
        'local_time': local.strftime("%Y-%m-%d %H:%M:%S"),
        'timezone_name': str(local.tzinfo) if hasattr(local, 'tzinfo') else 'Local',
        'utc_offset': local.strftime("%Z"),
        'us_market_time': get_us_market_time(),
        'hk_time': get_hk_time(),
        'hk_market_time': get_hk_market_time()
    }