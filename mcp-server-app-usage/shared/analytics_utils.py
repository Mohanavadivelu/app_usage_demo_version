"""
Analytics utilities for MCP App Usage Analytics Server.

This module provides helper functions for data analysis, calculations,
and formatting used throughout the analytics system.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from .models import RankingResult, TimeSeriesData
import statistics


def calculate_percentages(data: List[Dict[str, Any]], value_field: str) -> List[Dict[str, Any]]:
    """
    Calculate percentages for a list of data records.
    
    This function adds a 'percentage' field to each record based on
    the specified value field relative to the total.
    
    Args:
        data (list): List of data dictionaries
        value_field (str): Field name containing the values to calculate percentages for
    
    Returns:
        list: Data with percentage field added
    
    Example:
        >>> data = [{'app': 'Chrome', 'hours': 10}, {'app': 'Firefox', 'hours': 5}]
        >>> result = calculate_percentages(data, 'hours')
        >>> print(result[0]['percentage'])
        66.67
    """
    if not data:
        return data
    
    # Calculate total
    total = sum(record.get(value_field, 0) for record in data)
    
    if total == 0:
        # If total is 0, set all percentages to 0
        for record in data:
            record['percentage'] = 0.0
        return data
    
    # Calculate percentages
    result = []
    for record in data.copy():
        record = record.copy()  # Don't modify original
        value = record.get(value_field, 0)
        percentage = (value / total) * 100
        record['percentage'] = round(percentage, 2)
        result.append(record)
    
    return result


def rank_results(
    data: List[Dict[str, Any]], 
    value_field: str, 
    name_field: str = 'name',
    limit: Optional[int] = None,
    reverse: bool = True
) -> List[RankingResult]:
    """
    Rank data records and return as RankingResult objects.
    
    Args:
        data (list): List of data dictionaries
        value_field (str): Field name to rank by
        name_field (str): Field name containing the item name
        limit (int, optional): Maximum number of results to return
        reverse (bool): True for descending order (highest first)
    
    Returns:
        list: List of RankingResult objects
    
    Example:
        >>> data = [{'name': 'Chrome', 'usage': 100}, {'name': 'Firefox', 'usage': 50}]
        >>> rankings = rank_results(data, 'usage', 'name', limit=5)
        >>> print(rankings[0].rank, rankings[0].name, rankings[0].value)
        1 Chrome 100
    """
    if not data:
        return []
    
    # Sort data by value field
    sorted_data = sorted(data, key=lambda x: x.get(value_field, 0), reverse=reverse)
    
    # Apply limit if specified
    if limit:
        sorted_data = sorted_data[:limit]
    
    # Calculate total for percentages
    total = sum(record.get(value_field, 0) for record in data)
    
    # Create ranking results
    rankings = []
    for i, record in enumerate(sorted_data, 1):
        value = record.get(value_field, 0)
        percentage = (value / total * 100) if total > 0 else 0
        
        # Extract additional data (exclude name and value fields)
        additional_data = {k: v for k, v in record.items() 
                          if k not in [name_field, value_field]}
        
        ranking = RankingResult(
            rank=i,
            name=record.get(name_field, 'Unknown'),
            value=value,
            percentage=percentage,
            additional_data=additional_data
        )
        rankings.append(ranking)
    
    return rankings


def aggregate_data(
    data: List[Dict[str, Any]], 
    group_by: str, 
    aggregations: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Aggregate data by grouping and applying aggregation functions.
    
    Args:
        data (list): List of data dictionaries
        group_by (str): Field name to group by
        aggregations (dict): Aggregation functions {field: function}
                           Functions: 'sum', 'avg', 'count', 'min', 'max'
    
    Returns:
        list: Aggregated data
    
    Example:
        >>> data = [
        ...     {'user': 'john', 'hours': 5, 'sessions': 3},
        ...     {'user': 'john', 'hours': 3, 'sessions': 2},
        ...     {'user': 'jane', 'hours': 8, 'sessions': 4}
        ... ]
        >>> result = aggregate_data(data, 'user', {'hours': 'sum', 'sessions': 'avg'})
        >>> print(result)
        [{'user': 'john', 'hours': 8, 'sessions': 2.5}, {'user': 'jane', 'hours': 8, 'sessions': 4.0}]
    """
    if not data:
        return []
    
    # Group data
    groups = {}
    for record in data:
        key = record.get(group_by)
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    
    # Apply aggregations
    result = []
    for group_key, group_records in groups.items():
        aggregated = {group_by: group_key}
        
        for field, func in aggregations.items():
            values = [record.get(field, 0) for record in group_records if record.get(field) is not None]
            
            if not values:
                aggregated[field] = 0
                continue
            
            if func == 'sum':
                aggregated[field] = sum(values)
            elif func == 'avg':
                aggregated[field] = sum(values) / len(values)
            elif func == 'count':
                aggregated[field] = len(values)
            elif func == 'min':
                aggregated[field] = min(values)
            elif func == 'max':
                aggregated[field] = max(values)
            else:
                raise ValueError(f"Unknown aggregation function: {func}")
        
        result.append(aggregated)
    
    return result


def format_duration(seconds: Union[int, float], format_type: str = "human") -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds (int or float): Duration in seconds
        format_type (str): Format type ('human', 'hms', 'hours', 'minutes')
    
    Returns:
        str: Formatted duration string
    
    Example:
        >>> formatted = format_duration(3665, "human")
        >>> print(formatted)
        1 hour, 1 minute, 5 seconds
        
        >>> formatted = format_duration(3665, "hms")
        >>> print(formatted)
        01:01:05
    """
    if seconds < 0:
        return "0 seconds"
    
    if format_type == "hours":
        hours = seconds / 3600
        return f"{hours:.2f} hours"
    
    elif format_type == "minutes":
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    
    elif format_type == "hms":
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    elif format_type == "human":
        if seconds < 60:
            return f"{int(seconds)} seconds"
        
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes} minutes, {remaining_seconds} seconds"
            else:
                return f"{minutes} minutes"
        
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if remaining_minutes > 0:
            parts.append(f"{remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}")
        if remaining_seconds > 0:
            parts.append(f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}")
        
        return ", ".join(parts)
    
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def calculate_growth_rate(current_value: float, previous_value: float) -> float:
    """
    Calculate growth rate percentage between two values.
    
    Args:
        current_value (float): Current period value
        previous_value (float): Previous period value
    
    Returns:
        float: Growth rate as percentage (positive for growth, negative for decline)
    
    Example:
        >>> growth = calculate_growth_rate(120, 100)
        >>> print(growth)
        20.0
    """
    if previous_value == 0:
        return 100.0 if current_value > 0 else 0.0
    
    growth_rate = ((current_value - previous_value) / previous_value) * 100
    return round(growth_rate, 2)


def calculate_statistics(values: List[Union[int, float]]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.
    
    Args:
        values (list): List of numeric values
    
    Returns:
        dict: Dictionary containing statistical measures
    
    Example:
        >>> stats = calculate_statistics([1, 2, 3, 4, 5])
        >>> print(stats)
        {'count': 5, 'sum': 15, 'mean': 3.0, 'median': 3, 'min': 1, 'max': 5, 'std_dev': 1.58}
    """
    if not values:
        return {
            'count': 0,
            'sum': 0,
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std_dev': 0
        }
    
    # Filter out None values
    numeric_values = [v for v in values if v is not None]
    
    if not numeric_values:
        return {
            'count': 0,
            'sum': 0,
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std_dev': 0
        }
    
    return {
        'count': len(numeric_values),
        'sum': round(sum(numeric_values), 2),
        'mean': round(statistics.mean(numeric_values), 2),
        'median': round(statistics.median(numeric_values), 2),
        'min': min(numeric_values),
        'max': max(numeric_values),
        'std_dev': round(statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0, 2)
    }


def create_time_series(
    data: List[Dict[str, Any]], 
    date_field: str, 
    value_field: str,
    label: str,
    unit: str = ""
) -> TimeSeriesData:
    """
    Create a TimeSeriesData object from data records.
    
    Args:
        data (list): List of data dictionaries
        date_field (str): Field name containing dates
        value_field (str): Field name containing values
        label (str): Label for the time series
        unit (str): Unit of measurement
    
    Returns:
        TimeSeriesData: Time series data object
    
    Example:
        >>> data = [
        ...     {'date': '2024-01-01', 'usage': 100},
        ...     {'date': '2024-01-02', 'usage': 150}
        ... ]
        >>> ts = create_time_series(data, 'date', 'usage', 'Daily Usage', 'hours')
    """
    # Sort data by date
    sorted_data = sorted(data, key=lambda x: x.get(date_field, ''))
    
    timestamps = [record.get(date_field, '') for record in sorted_data]
    values = [record.get(value_field, 0) for record in sorted_data]
    
    return TimeSeriesData(
        timestamps=timestamps,
        values=values,
        label=label,
        unit=unit
    )


def calculate_moving_average(values: List[Union[int, float]], window_size: int) -> List[float]:
    """
    Calculate moving average for a list of values.
    
    Args:
        values (list): List of numeric values
        window_size (int): Size of the moving window
    
    Returns:
        list: List of moving averages
    
    Example:
        >>> values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> ma = calculate_moving_average(values, 3)
        >>> print(ma[:3])
        [2.0, 3.0, 4.0]
    """
    if len(values) < window_size:
        return []
    
    moving_averages = []
    for i in range(window_size - 1, len(values)):
        window = values[i - window_size + 1:i + 1]
        avg = sum(window) / window_size
        moving_averages.append(round(avg, 2))
    
    return moving_averages


def find_outliers(values: List[Union[int, float]], method: str = "iqr") -> List[int]:
    """
    Find outliers in a list of values.
    
    Args:
        values (list): List of numeric values
        method (str): Method to use ('iqr' or 'zscore')
    
    Returns:
        list: List of indices where outliers are found
    
    Example:
        >>> values = [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        >>> outliers = find_outliers(values, "iqr")
        >>> print(outliers)
        [5]
    """
    if len(values) < 4:
        return []
    
    outlier_indices = []
    
    if method == "iqr":
        # Interquartile Range method
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_index = n // 4
        q3_index = 3 * n // 4
        
        q1 = sorted_values[q1_index]
        q3 = sorted_values[q3_index]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
    
    elif method == "zscore":
        # Z-score method
        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return []
        
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_dev)
            if z_score > 2:  # Threshold of 2 standard deviations
                outlier_indices.append(i)
    
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")
    
    return outlier_indices


def normalize_values(values: List[Union[int, float]], method: str = "min_max") -> List[float]:
    """
    Normalize values to a standard range.
    
    Args:
        values (list): List of numeric values
        method (str): Normalization method ('min_max' or 'z_score')
    
    Returns:
        list: List of normalized values
    
    Example:
        >>> values = [10, 20, 30, 40, 50]
        >>> normalized = normalize_values(values, "min_max")
        >>> print(normalized)
        [0.0, 0.25, 0.5, 0.75, 1.0]
    """
    if not values:
        return []
    
    if method == "min_max":
        min_val = min(values)
        max_val = max(values)
        
        if min_val == max_val:
            return [0.5] * len(values)  # All values are the same
        
        range_val = max_val - min_val
        return [round((v - min_val) / range_val, 4) for v in values]
    
    elif method == "z_score":
        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 1
        
        return [round((v - mean_val) / std_dev, 4) for v in values]
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two sets of values.
    
    Args:
        x_values (list): First set of values
        y_values (list): Second set of values
    
    Returns:
        float: Correlation coefficient (-1 to 1)
    
    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 6, 8, 10]
        >>> corr = calculate_correlation(x, y)
        >>> print(corr)
        1.0
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0
    
    try:
        correlation = statistics.correlation(x_values, y_values)
        return round(correlation, 4)
    except statistics.StatisticsError:
        return 0.0
