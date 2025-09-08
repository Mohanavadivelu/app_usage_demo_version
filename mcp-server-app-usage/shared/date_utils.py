"""
Date and time utilities for MCP App Usage Analytics Server.

This module provides helper functions for date parsing, formatting,
and time period calculations used throughout the analytics system.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional, Union
import calendar


def parse_date(date_string: str, format_string: str = "%Y-%m-%d") -> date:
    """
    Parse a date string into a date object.
    
    Args:
        date_string (str): Date string to parse
        format_string (str): Expected date format (default: YYYY-MM-DD)
    
    Returns:
        date: Parsed date object
    
    Raises:
        ValueError: If date string is invalid
    
    Example:
        >>> parsed = parse_date("2024-01-15")
        >>> print(parsed)
        2024-01-15
    """
    try:
        return datetime.strptime(date_string, format_string).date()
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_string}'. Expected format: {format_string}") from e


def format_date(date_obj: Union[date, datetime], format_string: str = "%Y-%m-%d") -> str:
    """
    Format a date object as a string.
    
    Args:
        date_obj (date or datetime): Date object to format
        format_string (str): Output format string
    
    Returns:
        str: Formatted date string
    
    Example:
        >>> formatted = format_date(date(2024, 1, 15))
        >>> print(formatted)
        2024-01-15
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_string)
    return date_obj.strftime(format_string)


def get_date_range(start_date: str, end_date: str) -> Tuple[date, date]:
    """
    Parse and validate a date range.
    
    Args:
        start_date (str): Start date string (YYYY-MM-DD)
        end_date (str): End date string (YYYY-MM-DD)
    
    Returns:
        tuple: (start_date_obj, end_date_obj)
    
    Raises:
        ValueError: If dates are invalid or start_date > end_date
    
    Example:
        >>> start, end = get_date_range("2024-01-01", "2024-01-31")
        >>> print(f"Range: {start} to {end}")
        Range: 2024-01-01 to 2024-01-31
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if start > end:
        raise ValueError("Start date cannot be after end date")
    
    return start, end


def calculate_time_periods(
    reference_date: Optional[Union[str, date]] = None
) -> dict:
    """
    Calculate common time periods relative to a reference date.
    
    This function calculates useful date ranges like "last 7 days",
    "last 30 days", "this month", etc., commonly used in analytics.
    
    Args:
        reference_date (str or date, optional): Reference date (defaults to today)
    
    Returns:
        dict: Dictionary of time period ranges
    
    Example:
        >>> periods = calculate_time_periods()
        >>> print(periods['last_7_days'])
        ('2024-01-08', '2024-01-15')
    """
    if reference_date is None:
        ref_date = date.today()
    elif isinstance(reference_date, str):
        ref_date = parse_date(reference_date)
    else:
        ref_date = reference_date
    
    periods = {}
    
    # Today
    periods['today'] = (format_date(ref_date), format_date(ref_date))
    
    # Yesterday
    yesterday = ref_date - timedelta(days=1)
    periods['yesterday'] = (format_date(yesterday), format_date(yesterday))
    
    # Last N days (including today)
    for days in [7, 14, 30, 60, 90]:
        start_date = ref_date - timedelta(days=days-1)
        periods[f'last_{days}_days'] = (format_date(start_date), format_date(ref_date))
    
    # This week (Monday to Sunday)
    days_since_monday = ref_date.weekday()
    week_start = ref_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    periods['this_week'] = (format_date(week_start), format_date(week_end))
    
    # Last week
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    periods['last_week'] = (format_date(last_week_start), format_date(last_week_end))
    
    # This month
    month_start = ref_date.replace(day=1)
    next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
    month_end = next_month - timedelta(days=1)
    periods['this_month'] = (format_date(month_start), format_date(month_end))
    
    # Last month
    if month_start.month == 1:
        last_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        last_month_start = month_start.replace(month=month_start.month - 1)
    
    last_month_end = month_start - timedelta(days=1)
    periods['last_month'] = (format_date(last_month_start), format_date(last_month_end))
    
    # This year
    year_start = ref_date.replace(month=1, day=1)
    year_end = ref_date.replace(month=12, day=31)
    periods['this_year'] = (format_date(year_start), format_date(year_end))
    
    # Last year
    last_year_start = year_start.replace(year=year_start.year - 1)
    last_year_end = year_start - timedelta(days=1)
    periods['last_year'] = (format_date(last_year_start), format_date(last_year_end))
    
    return periods


def get_days_between(start_date: str, end_date: str) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        start_date (str): Start date string (YYYY-MM-DD)
        end_date (str): End date string (YYYY-MM-DD)
    
    Returns:
        int: Number of days between dates (inclusive)
    
    Example:
        >>> days = get_days_between("2024-01-01", "2024-01-31")
        >>> print(days)
        31
    """
    start, end = get_date_range(start_date, end_date)
    return (end - start).days + 1


def generate_date_series(start_date: str, end_date: str, interval: str = "day") -> List[str]:
    """
    Generate a series of dates between start and end dates.
    
    Args:
        start_date (str): Start date string (YYYY-MM-DD)
        end_date (str): End date string (YYYY-MM-DD)
        interval (str): Interval type ("day", "week", "month")
    
    Returns:
        list: List of date strings
    
    Example:
        >>> dates = generate_date_series("2024-01-01", "2024-01-05")
        >>> print(dates)
        ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    """
    start, end = get_date_range(start_date, end_date)
    dates = []
    current = start
    
    if interval == "day":
        while current <= end:
            dates.append(format_date(current))
            current += timedelta(days=1)
    
    elif interval == "week":
        # Start from the Monday of the start date's week
        days_since_monday = current.weekday()
        current = current - timedelta(days=days_since_monday)
        
        while current <= end:
            dates.append(format_date(current))
            current += timedelta(days=7)
    
    elif interval == "month":
        while current <= end:
            dates.append(format_date(current))
            # Move to first day of next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
    
    else:
        raise ValueError("Interval must be 'day', 'week', or 'month'")
    
    return dates


def get_week_boundaries(date_string: str) -> Tuple[str, str]:
    """
    Get the start and end dates of the week containing the given date.
    
    Args:
        date_string (str): Date string (YYYY-MM-DD)
    
    Returns:
        tuple: (week_start, week_end) as strings
    
    Example:
        >>> start, end = get_week_boundaries("2024-01-15")  # Monday
        >>> print(f"Week: {start} to {end}")
        Week: 2024-01-15 to 2024-01-21
    """
    date_obj = parse_date(date_string)
    days_since_monday = date_obj.weekday()
    
    week_start = date_obj - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return format_date(week_start), format_date(week_end)


def get_month_boundaries(date_string: str) -> Tuple[str, str]:
    """
    Get the start and end dates of the month containing the given date.
    
    Args:
        date_string (str): Date string (YYYY-MM-DD)
    
    Returns:
        tuple: (month_start, month_end) as strings
    
    Example:
        >>> start, end = get_month_boundaries("2024-01-15")
        >>> print(f"Month: {start} to {end}")
        Month: 2024-01-01 to 2024-01-31
    """
    date_obj = parse_date(date_string)
    
    month_start = date_obj.replace(day=1)
    
    # Get last day of month
    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
    month_end = date_obj.replace(day=last_day)
    
    return format_date(month_start), format_date(month_end)


def is_weekend(date_string: str) -> bool:
    """
    Check if a date falls on a weekend (Saturday or Sunday).
    
    Args:
        date_string (str): Date string (YYYY-MM-DD)
    
    Returns:
        bool: True if weekend, False otherwise
    
    Example:
        >>> is_weekend("2024-01-13")  # Saturday
        True
        >>> is_weekend("2024-01-15")  # Monday
        False
    """
    date_obj = parse_date(date_string)
    return date_obj.weekday() >= 5  # Saturday=5, Sunday=6


def get_business_days(start_date: str, end_date: str) -> List[str]:
    """
    Get all business days (Monday-Friday) between two dates.
    
    Args:
        start_date (str): Start date string (YYYY-MM-DD)
        end_date (str): End date string (YYYY-MM-DD)
    
    Returns:
        list: List of business day date strings
    
    Example:
        >>> business_days = get_business_days("2024-01-15", "2024-01-19")
        >>> print(business_days)
        ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
    """
    dates = generate_date_series(start_date, end_date, "day")
    return [date_str for date_str in dates if not is_weekend(date_str)]


def get_quarter_boundaries(date_string: str) -> Tuple[str, str]:
    """
    Get the start and end dates of the quarter containing the given date.
    
    Args:
        date_string (str): Date string (YYYY-MM-DD)
    
    Returns:
        tuple: (quarter_start, quarter_end) as strings
    
    Example:
        >>> start, end = get_quarter_boundaries("2024-02-15")
        >>> print(f"Q1: {start} to {end}")
        Q1: 2024-01-01 to 2024-03-31
    """
    date_obj = parse_date(date_string)
    
    # Determine quarter
    quarter = (date_obj.month - 1) // 3 + 1
    
    # Calculate quarter start
    quarter_start_month = (quarter - 1) * 3 + 1
    quarter_start = date_obj.replace(month=quarter_start_month, day=1)
    
    # Calculate quarter end
    quarter_end_month = quarter * 3
    if quarter_end_month == 12:
        quarter_end = date_obj.replace(month=12, day=31)
    else:
        next_quarter_start = date_obj.replace(month=quarter_end_month + 1, day=1)
        quarter_end = next_quarter_start - timedelta(days=1)
    
    return format_date(quarter_start), format_date(quarter_end)


def days_ago(days: int, reference_date: Optional[Union[str, date]] = None) -> str:
    """
    Get the date that was N days ago from a reference date.
    
    Args:
        days (int): Number of days ago
        reference_date (str or date, optional): Reference date (defaults to today)
    
    Returns:
        str: Date string N days ago
    
    Example:
        >>> past_date = days_ago(7)  # 7 days ago from today
        >>> print(past_date)
        2024-01-08
    """
    if reference_date is None:
        ref_date = date.today()
    elif isinstance(reference_date, str):
        ref_date = parse_date(reference_date)
    else:
        ref_date = reference_date
    
    past_date = ref_date - timedelta(days=days)
    return format_date(past_date)


def get_hour_from_timestamp(timestamp: str) -> int:
    """
    Extract hour from a timestamp string.
    
    Args:
        timestamp (str): Timestamp string (various formats supported)
    
    Returns:
        int: Hour (0-23)
    
    Example:
        >>> hour = get_hour_from_timestamp("2024-01-15 14:30:00")
        >>> print(hour)
        14
    """
    # Try different timestamp formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp, fmt)
            return dt.hour
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse timestamp: {timestamp}")
