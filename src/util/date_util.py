"""Date utility functions for handling timezone-aware date operations."""

from datetime import datetime
from zoneinfo import ZoneInfo


def get_hk_timezone():
    """Get Hong Kong timezone object.
    
    Returns:
        ZoneInfo: Hong Kong timezone object
    """
    return ZoneInfo('Asia/Hong_Kong')


def get_current_date_hk(date_format="%Y-%m-%d"):
    """Get current date in Hong Kong timezone.
    
    Args:
        date_format (str): Date format string. Defaults to "%Y-%m-%d".
        
    Returns:
        str: Current date in Hong Kong timezone formatted as string
    """
    hk_timezone = get_hk_timezone()
    return datetime.now(hk_timezone).strftime(date_format)


def get_current_datetime_hk():
    """Get current datetime in Hong Kong timezone.
    
    Returns:
        datetime: Current datetime in Hong Kong timezone
    """
    hk_timezone = get_hk_timezone()
    return datetime.now(hk_timezone) 