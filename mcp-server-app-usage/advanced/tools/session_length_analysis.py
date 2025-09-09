"""
Tool: Session Length Analysis
Category: Advanced
Feature ID: 37

Description:
    Average session length per user/app. This tool provides comprehensive
    analysis of session durations across users and applications, helping
    identify usage patterns and engagement levels.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - user_filter (str, optional): Filter by specific user
    - sort_by (str, optional): Sort field (avg_session_length, total_sessions, user)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with session length analysis and statistics

Examples:
    Basic usage:
    Input: {}
    Output: Session length analysis for all users and applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "limit": 50}
    Output: Chrome session length analysis for top 50 results

Database Tables Used:
    - app_usage: For session duration data

Related Tools:
    - median_session_length: Calculate median session lengths
    - heavy_users: Identify users with long sessions

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def session_length_analysis(
    limit: int = 100,
    app_name: Optional[str] = None,
    user_filter: Optional[str] = None,
    sort_by: str = "avg_session_length",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Analyze average session length per user/app.
    
    Args:
        limit: Maximum number of results to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        user_filter: Filter by specific user
        sort_by: Field to sort by (avg_session_length, total_sessions, user, total_hours)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing session length analysis and statistics
    """
    try:
        if ctx:
            filter_desc = []
            if app_name:
                filter_desc.append(f"app: {app_name}")
            if user_filter:
                filter_desc.append(f"user: {user_filter}")
            filter_str = f" with filters: {', '.join(filter_desc)}" if filter_desc else ""
            ctx.info(f"Analyzing session lengths{filter_str}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['avg_session_length', 'total_sessions', 'user', 'total_hours']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Build query for session length analysis
        base_query = """
        SELECT 
            user,
            application_name,
            COUNT(*) as total_sessions,
            SUM(duration_seconds) as total_seconds,
            AVG(duration_seconds) as avg_session_seconds,
            MIN(duration_seconds) as min_session_seconds,
            MAX(duration_seconds) as max_session_seconds,
            MIN(log_date) as first_session_date,
            MAX(log_date) as last_session_date
        FROM app_usage
        WHERE duration_seconds > 0
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        if user_filter:
            filters['user'] = user_filter
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'avg_session_length': 'avg_session_seconds',
            'total_sessions': 'total_sessions',
            'user': 'user',
            'total_hours': 'total_seconds'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="user, application_name",
            order_by=order_clause,
            limit=limit
        )
        
        if ctx:
            ctx.debug("Executing session length analysis query")
            ctx.report_progress(25, 100, "Querying session length data...")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} session records in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing session length analysis...")
        
        # Format response
        response_data = {
            "tool": "session_length_analysis",
            "description": "Average session length per user/app analysis",
            "query_time_ms": result.query_time_ms,
            "total_records": result.total_count,
            "filters_applied": {
                "app_name": app_name,
                "user_filter": user_filter,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "session_analysis": []
        }
        
        # Process session length data
        total_sessions = 0
        total_hours = 0
        unique_users = set()
        unique_apps = set()
        session_lengths = []
        
        for record in result.data:
            total_seconds = record["total_seconds"] or 0
            avg_session_seconds = record["avg_session_seconds"] or 0
            total_hours_for_record = total_seconds / 3600
            avg_session_minutes = avg_session_seconds / 60
            min_session_minutes = (record["min_session_seconds"] or 0) / 60
            max_session_minutes = (record["max_session_seconds"] or 0) / 60
            
            total_sessions += record["total_sessions"]
            total_hours += total_hours_for_record
            unique_users.add(record["user"])
            unique_apps.add(record["application_name"])
            session_lengths.append(avg_session_seconds)
            
            session_info = {
                "user": record["user"],
                "application_name": record["application_name"],
                "session_statistics": {
                    "total_sessions": record["total_sessions"],
                    "total_hours": round(total_hours_for_record, 2),
                    "average_session_minutes": round(avg_session_minutes, 2),
                    "min_session_minutes": round(min_session_minutes, 2),
                    "max_session_minutes": round(max_session_minutes, 2),
                    "first_session_date": record["first_session_date"],
                    "last_session_date": record["last_session_date"]
                },
                "engagement_level": _categorize_engagement(avg_session_minutes)
            }
            response_data["session_analysis"].append(session_info)
        
        # Calculate overall statistics
        if session_lengths:
            session_lengths.sort()
            median_length = session_lengths[len(session_lengths) // 2] / 60  # Convert to minutes
            overall_avg = sum(session_lengths) / len(session_lengths) / 60  # Convert to minutes
        else:
            median_length = 0
            overall_avg = 0
        
        # Add summary statistics
        response_data["summary"] = {
            "total_sessions_analyzed": total_sessions,
            "total_usage_hours": round(total_hours, 2),
            "unique_users": len(unique_users),
            "unique_applications": len(unique_apps),
            "overall_statistics": {
                "average_session_minutes": round(overall_avg, 2),
                "median_session_minutes": round(median_length, 2),
                "total_user_app_combinations": len(result.data)
            },
            "engagement_distribution": _calculate_engagement_distribution(response_data["session_analysis"])
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Session length analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} records, {total_sessions} sessions, avg {overall_avg:.1f} min")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in session_length_analysis: {e}")
        if ctx:
            ctx.error(f"Failed to analyze session lengths: {e}")
        
        return {
            "tool": "session_length_analysis",
            "error": str(e),
            "message": "Failed to analyze session lengths"
        }


def _categorize_engagement(avg_session_minutes: float) -> str:
    """Categorize user engagement based on average session length."""
    if avg_session_minutes < 5:
        return "low"
    elif avg_session_minutes < 30:
        return "moderate"
    elif avg_session_minutes < 120:
        return "high"
    else:
        return "very_high"


def _calculate_engagement_distribution(session_analysis: list) -> Dict[str, int]:
    """Calculate distribution of engagement levels."""
    distribution = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
    for session in session_analysis:
        level = session["engagement_level"]
        distribution[level] += 1
    return distribution
