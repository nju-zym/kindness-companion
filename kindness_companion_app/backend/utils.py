import datetime
import logging
import os
from pathlib import Path


def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration.
    
    Args:
        log_level (int, optional): Logging level. Default is INFO.
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory
    log_dir = Path.home() / ".kindness_challenge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file name with current date
    today = datetime.date.today().isoformat()
    log_file = log_dir / f"kindness_challenge_{today}.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("kindness_challenge")


def format_date(date_str, output_format="%Y-%m-%d"):
    """
    Format a date string.
    
    Args:
        date_str (str): Date string in ISO format (YYYY-MM-DD)
        output_format (str, optional): Output date format
        
    Returns:
        str: Formatted date string
    """
    date_obj = datetime.date.fromisoformat(date_str)
    return date_obj.strftime(output_format)


def get_day_of_week(date_str):
    """
    Get the day of the week for a date.
    
    Args:
        date_str (str): Date string in ISO format (YYYY-MM-DD)
        
    Returns:
        str: Day of the week (e.g., "Monday")
    """
    date_obj = datetime.date.fromisoformat(date_str)
    return date_obj.strftime("%A")


def get_date_range(days, end_date=None):
    """
    Get a range of dates.
    
    Args:
        days (int): Number of days in the range
        end_date (datetime.date, optional): End date. If None, today is used.
        
    Returns:
        list: List of date strings in ISO format (YYYY-MM-DD)
    """
    if end_date is None:
        end_date = datetime.date.today()
    
    date_range = []
    for i in range(days):
        date = end_date - datetime.timedelta(days=i)
        date_range.append(date.isoformat())
    
    return date_range


def parse_time(time_str):
    """
    Parse a time string.
    
    Args:
        time_str (str): Time string in HH:MM format (24-hour)
        
    Returns:
        tuple: (hour, minute)
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            return hour, minute
    except ValueError:
        pass
    
    return None


def format_time(hour, minute):
    """
    Format hour and minute as a time string.
    
    Args:
        hour (int): Hour (0-23)
        minute (int): Minute (0-59)
        
    Returns:
        str: Time string in HH:MM format
    """
    return f"{hour:02d}:{minute:02d}"


def get_day_name(day_number):
    """
    Get the name of a day of the week.
    
    Args:
        day_number (int): Day number (0-6, where 0 is Monday)
        
    Returns:
        str: Day name
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[day_number % 7]


def get_day_names(day_numbers):
    """
    Get the names of days of the week.
    
    Args:
        day_numbers (list): List of day numbers (0-6, where 0 is Monday)
        
    Returns:
        list: List of day names
    """
    return [get_day_name(day) for day in day_numbers]
