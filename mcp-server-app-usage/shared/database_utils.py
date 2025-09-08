"""
Database utilities for MCP App Usage Analytics Server.

This module provides helper functions for building queries, executing
analytics operations, and validating parameters.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from config.database import get_database_connection, DatabaseConfig
from .models import AnalyticsResult
import logging

logger = logging.getLogger(__name__)


def build_query(
    base_query: str,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    group_by: Optional[str] = None
) -> Tuple[str, tuple]:
    """
    Build a SQL query with optional filters, ordering, and limiting.
    
    This utility function helps construct complex queries by combining
    a base query with common clauses like WHERE, ORDER BY, and LIMIT.
    
    Args:
        base_query (str): Base SQL query
        filters (dict, optional): Dictionary of column:value filters
        order_by (str, optional): ORDER BY clause
        limit (int, optional): LIMIT value
        group_by (str, optional): GROUP BY clause
    
    Returns:
        tuple: (complete_query, parameters_tuple)
    
    Example:
        >>> query, params = build_query(
        ...     "SELECT * FROM app_usage",
        ...     filters={"user": "john", "platform": "Windows"},
        ...     order_by="log_date DESC",
        ...     limit=100
        ... )
        >>> print(query)
        SELECT * FROM app_usage WHERE user = ? AND platform = ? ORDER BY log_date DESC LIMIT 100
    """
    query_parts = [base_query]
    params = []
    
    # Add WHERE clause if filters provided
    if filters:
        where_conditions = []
        for column, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    # Handle IN clause for lists
                    placeholders = ','.join(['?' for _ in value])
                    where_conditions.append(f"{column} IN ({placeholders})")
                    params.extend(value)
                elif isinstance(value, tuple) and len(value) == 2:
                    # Handle range queries (min, max)
                    where_conditions.append(f"{column} BETWEEN ? AND ?")
                    params.extend(value)
                else:
                    where_conditions.append(f"{column} = ?")
                    params.append(value)
        
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))
    
    # Add GROUP BY clause
    if group_by:
        query_parts.append(f"GROUP BY {group_by}")
    
    # Add ORDER BY clause
    if order_by:
        query_parts.append(f"ORDER BY {order_by}")
    
    # Add LIMIT clause
    if limit:
        query_parts.append(f"LIMIT {limit}")
    
    complete_query = " ".join(query_parts)
    return complete_query, tuple(params)


def execute_analytics_query(
    query: str,
    params: tuple = (),
    config: Optional[DatabaseConfig] = None
) -> AnalyticsResult:
    """
    Execute an analytics query and return structured results.
    
    This function executes a query, measures execution time, and returns
    results in a standardized AnalyticsResult format.
    
    Args:
        query (str): SQL query to execute
        params (tuple): Query parameters
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        AnalyticsResult: Structured query results with metadata
    
    Raises:
        DatabaseError: If query execution fails
    """
    start_time = time.time()
    
    try:
        with get_database_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert sqlite3.Row objects to dictionaries
            data = [dict(row) for row in rows]
            
            end_time = time.time()
            query_time_ms = (end_time - start_time) * 1000
            
            logger.debug(f"Query executed in {query_time_ms:.2f}ms, returned {len(data)} rows")
            
            return AnalyticsResult(
                data=data,
                total_count=len(data),
                query_time_ms=query_time_ms,
                metadata={
                    'query': query,
                    'params': params,
                    'execution_time': query_time_ms
                }
            )
    
    except sqlite3.Error as e:
        logger.error(f"Database error executing query: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        raise


def validate_parameters(params: Dict[str, Any], required: List[str], optional: List[str] = None) -> Dict[str, Any]:
    """
    Validate and sanitize input parameters.
    
    This function checks that required parameters are present and validates
    parameter types and values according to business rules.
    
    Args:
        params (dict): Input parameters to validate
        required (list): List of required parameter names
        optional (list, optional): List of optional parameter names
    
    Returns:
        dict: Validated and sanitized parameters
    
    Raises:
        ValueError: If validation fails
    
    Example:
        >>> validated = validate_parameters(
        ...     {"user": "john", "limit": "10"},
        ...     required=["user"],
        ...     optional=["limit"]
        ... )
        >>> print(validated)
        {'user': 'john', 'limit': 10}
    """
    if optional is None:
        optional = []
    
    validated = {}
    
    # Check required parameters
    for param in required:
        if param not in params or params[param] is None:
            raise ValueError(f"Required parameter '{param}' is missing")
        validated[param] = params[param]
    
    # Process optional parameters
    for param in optional:
        if param in params and params[param] is not None:
            validated[param] = params[param]
    
    # Type conversion and validation
    for key, value in validated.items():
        validated[key] = _validate_parameter_value(key, value)
    
    return validated


def _validate_parameter_value(param_name: str, value: Any) -> Any:
    """
    Validate and convert individual parameter values.
    
    Args:
        param_name (str): Name of the parameter
        value (Any): Parameter value to validate
    
    Returns:
        Any: Validated and converted value
    
    Raises:
        ValueError: If validation fails
    """
    # Convert string numbers to integers for limit/count parameters
    if param_name in ['limit', 'top_n', 'days', 'months', 'hours']:
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Parameter '{param_name}' must be a positive integer")
        if param_name == 'limit' and value > 10000:
            raise ValueError("Limit cannot exceed 10000")
        if param_name == 'top_n' and value > 100:
            raise ValueError("top_n cannot exceed 100")
    
    # Validate date format
    elif param_name in ['start_date', 'end_date', 'date', 'log_date']:
        if not isinstance(value, str):
            raise ValueError(f"Parameter '{param_name}' must be a string")
        if not _is_valid_date_format(value):
            raise ValueError(f"Parameter '{param_name}' must be in YYYY-MM-DD format")
    
    # Validate user and app names
    elif param_name in ['user', 'user_id', 'application_name', 'app_name']:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Parameter '{param_name}' must be a non-empty string")
        value = value.strip()
    
    # Validate platform
    elif param_name == 'platform':
        valid_platforms = ['Windows', 'Linux', 'macOS', 'Android', 'iOS']
        if value not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
    
    # Validate boolean parameters
    elif param_name in ['legacy_app', 'enable_tracking']:
        if isinstance(value, str):
            value = value.lower() in ('true', '1', 'yes', 'on')
        elif not isinstance(value, bool):
            raise ValueError(f"Parameter '{param_name}' must be a boolean")
    
    return value


def _is_valid_date_format(date_string: str) -> bool:
    """
    Check if a string is in valid YYYY-MM-DD format.
    
    Args:
        date_string (str): Date string to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        from datetime import datetime
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_table_columns(table_name: str, config: Optional[DatabaseConfig] = None) -> List[str]:
    """
    Get column names for a database table.
    
    Args:
        table_name (str): Name of the table
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        list: List of column names
    """
    query = f"PRAGMA table_info({table_name})"
    
    with get_database_connection(config) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = cursor.fetchall()
        return [col[1] for col in columns]  # Column name is at index 1


def build_aggregation_query(
    table: str,
    select_fields: List[str],
    group_by: List[str],
    aggregations: Dict[str, str],
    filters: Optional[Dict[str, Any]] = None,
    having: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> Tuple[str, tuple]:
    """
    Build complex aggregation queries.
    
    Args:
        table (str): Table name
        select_fields (list): Fields to select (non-aggregated)
        group_by (list): Fields to group by
        aggregations (dict): Aggregation functions {alias: expression}
        filters (dict, optional): WHERE clause filters
        having (str, optional): HAVING clause
        order_by (str, optional): ORDER BY clause
        limit (int, optional): LIMIT value
    
    Returns:
        tuple: (query, parameters)
    
    Example:
        >>> query, params = build_aggregation_query(
        ...     table="app_usage",
        ...     select_fields=["user", "application_name"],
        ...     group_by=["user", "application_name"],
        ...     aggregations={"total_hours": "SUM(duration_seconds)/3600.0"},
        ...     filters={"platform": "Windows"},
        ...     order_by="total_hours DESC",
        ...     limit=10
        ... )
    """
    # Build SELECT clause
    select_parts = select_fields.copy()
    for alias, expression in aggregations.items():
        select_parts.append(f"{expression} as {alias}")
    
    base_query = f"SELECT {', '.join(select_parts)} FROM {table}"
    
    return build_query(
        base_query=base_query,
        filters=filters,
        group_by=', '.join(group_by) if group_by else None,
        order_by=order_by,
        limit=limit
    )


def execute_batch_queries(queries: List[Tuple[str, tuple]], config: Optional[DatabaseConfig] = None) -> List[AnalyticsResult]:
    """
    Execute multiple queries in a single database connection.
    
    Args:
        queries (list): List of (query, params) tuples
        config (DatabaseConfig, optional): Database configuration
    
    Returns:
        list: List of AnalyticsResult objects
    """
    results = []
    
    with get_database_connection(config) as conn:
        for query, params in queries:
            start_time = time.time()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            end_time = time.time()
            query_time_ms = (end_time - start_time) * 1000
            
            results.append(AnalyticsResult(
                data=data,
                total_count=len(data),
                query_time_ms=query_time_ms,
                metadata={'query': query, 'params': params}
            ))
    
    return results
