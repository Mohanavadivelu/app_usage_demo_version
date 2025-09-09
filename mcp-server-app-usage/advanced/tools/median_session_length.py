"""
Tool: Median Session Length
Category: Advanced
Feature ID: 38

Description:
    Calculate median session length for applications and users.
    This tool provides more robust session duration statistics by
    using median values, which are less affected by outliers.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - user_filter (str, optional): Filter by specific user
    - sort_by (str, optional): Sort field (median_minutes, total_sessions, user)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with median session length analysis

Examples:
    Basic usage:
    Input: {}
    Output: Median session lengths for all users and applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "limit": 50}
    Output: Chrome median session lengths for top 50 results

Database Tables Used:
    - app_usage: For session duration data

Related Tools:
    - session_length_analysis: Compare with average session lengths
    - heavy_users: Analyze session patterns of power users

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
async def median_session_length(
    limit: int = 100,
    app_name: Optional[str] = None,
    user_filter: Optional[str] = None,
    sort_by: str = "median_minutes",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Calculate median session length for applications and users.
    
    Args:
        limit: Maximum number of results to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        user_filter: Filter by specific user
        sort_by: Field to sort by (median_minutes, total_sessions, user, total_hours)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing median session length analysis
    """
    try:
        if ctx:
            filter_desc = []
            if app_name:
                filter_desc.append(f"app: {app_name}")
            if user_filter:
                filter_desc.append(f"user: {user_filter}")
            filter_str = f" with filters: {', '.join(filter_desc)}" if filter_desc else ""
            ctx.info(f"Calculating median session lengths{filter_str}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['median_minutes', 'total_sessions', 'user', 'total_hours']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        if ctx:
            ctx.report_progress(25, 100, "Calculating median session lengths...")
        
        # Build query for median session length calculation
        # SQLite doesn't have a built-in MEDIAN function, so we'll use percentile approach
        base_query = """
        WITH session_data AS (
            SELECT 
                user,
                application_name,
                duration_seconds,
                ROW_NUMBER() OVER (PARTITION BY user, application_name ORDER BY duration_seconds) as row_num,
                COUNT(*) OVER (PARTITION BY user, application_name) as total_sessions
            FROM app_usage
            WHERE duration_seconds > 0
        ),
        median_calculations AS (
            SELECT 
                user,
                application_name,
                total_sessions,
                AVG(duration_seconds) as median_seconds
            FROM session_data
            WHERE row_num IN (
                (total_sessions + 1) / 2,
                (total_sessions + 2) / 2
            )
            GROUP BY user, application_name, total_sessions
        ),
        session_stats AS (
            SELECT 
                mc.user,
                mc.application_name,
                mc.total_sessions,
                mc.median_seconds,
                SUM(sd.duration_seconds) as total_seconds,
                MIN(sd.duration_seconds) as min_seconds,
                MAX(sd.duration_seconds) as max_seconds,
                AVG(sd.duration_seconds) as avg_seconds
            FROM median_calculations mc
            JOIN (
                SELECT user, application_name, duration_seconds
                FROM app_usage 
                WHERE duration_seconds > 0
            ) sd ON mc.user = sd.user AND mc.application_name = sd.application_name
            GROUP BY mc.user, mc.application_name, mc.total_sessions, mc.median_seconds
        )
        SELECT 
            user,
            application_name,
            total_sessions,
            ROUND(median_seconds / 60.0, 2) as median_minutes,
            ROUND(total_seconds / 3600.0, 2) as total_hours,
            ROUND(avg_seconds / 60.0, 2) as avg_minutes,
            ROUND(min_seconds / 60.0, 2) as min_minutes,
            ROUND(max_seconds / 60.0, 2) as max_minutes
        FROM session_stats
        WHERE total_sessions >= 3
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        if user_filter:
            filters['user'] = user_filter
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'median_minutes': 'median_minutes',
            'total_sessions': 'total_sessions',
            'user': 'user',
            'total_hours': 'total_hours'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by=order_clause,
            limit=limit
        )
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} session records in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing median session analysis...")
        
        # Format response
        response_data = {
            "tool": "median_session_length",
            "description": "Median session length analysis",
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
        
        # Process median session data
        total_sessions = 0
        total_hours = 0
        unique_users = set()
        unique_apps = set()
        median_values = []
        avg_values = []
        
        for record in result.data:
            median_minutes = record["median_minutes"] or 0
            avg_minutes = record["avg_minutes"] or 0
            total_hours_for_record = record["total_hours"] or 0
            
            total_sessions += record["total_sessions"]
            total_hours += total_hours_for_record
            unique_users.add(record["user"])
            unique_apps.add(record["application_name"])
            median_values.append(median_minutes)
            avg_values.append(avg_minutes)
            
            # Calculate variance between median and average
            median_avg_diff = abs(median_minutes - avg_minutes)
            median_avg_ratio = (median_minutes / avg_minutes) if avg_minutes > 0 else 0
            
            # Categorize session length patterns
            if median_minutes < 5:
                session_pattern = "short_sessions"
            elif median_minutes < 30:
                session_pattern = "moderate_sessions"
            elif median_minutes < 120:
                session_pattern = "long_sessions"
            else:
                session_pattern = "very_long_sessions"
            
            # Generate insights based on median vs average comparison
            insights = []
            if median_avg_ratio < 0.7:
                insights.append("Median significantly lower than average - presence of outlier long sessions")
            elif median_avg_ratio > 1.3:
                insights.append("Median higher than average - unusual distribution pattern")
            else:
                insights.append("Median and average are similar - consistent session lengths")
            
            if median_minutes > 60:
                insights.append("Long median sessions indicate deep engagement")
            elif median_minutes < 2:
                insights.append("Very short median sessions may indicate usability issues")
            
            session_info = {
                "user": record["user"],
                "application_name": record["application_name"],
                "session_statistics": {
                    "total_sessions": record["total_sessions"],
                    "total_hours": total_hours_for_record,
                    "median_session_minutes": median_minutes,
                    "average_session_minutes": avg_minutes,
                    "min_session_minutes": record["min_minutes"],
                    "max_session_minutes": record["max_minutes"]
                },
                "distribution_analysis": {
                    "median_avg_difference_minutes": round(median_avg_diff, 2),
                    "median_to_average_ratio": round(median_avg_ratio, 2),
                    "session_pattern": session_pattern
                },
                "insights": insights
            }
            response_data["session_analysis"].append(session_info)
        
        # Calculate overall statistics
        if median_values:
            median_values.sort()
            overall_median = median_values[len(median_values) // 2]
            overall_avg_median = sum(median_values) / len(median_values)
            overall_avg_average = sum(avg_values) / len(avg_values)
        else:
            overall_median = 0
            overall_avg_median = 0
            overall_avg_average = 0
        
        # Add summary statistics
        response_data["summary"] = {
            "total_sessions_analyzed": total_sessions,
            "total_usage_hours": round(total_hours, 2),
            "unique_users": len(unique_users),
            "unique_applications": len(unique_apps),
            "overall_statistics": {
                "median_of_medians_minutes": round(overall_median, 2),
                "average_median_minutes": round(overall_avg_median, 2),
                "average_of_averages_minutes": round(overall_avg_average, 2),
                "total_user_app_combinations": len(result.data)
            }
        }
        
        # Add distribution insights
        short_sessions = len([s for s in response_data["session_analysis"] if s["distribution_analysis"]["session_pattern"] == "short_sessions"])
        moderate_sessions = len([s for s in response_data["session_analysis"] if s["distribution_analysis"]["session_pattern"] == "moderate_sessions"])
        long_sessions = len([s for s in response_data["session_analysis"] if s["distribution_analysis"]["session_pattern"] == "long_sessions"])
        very_long_sessions = len([s for s in response_data["session_analysis"] if s["distribution_analysis"]["session_pattern"] == "very_long_sessions"])
        
        response_data["distribution_insights"] = {
            "session_length_patterns": {
                "short_sessions": short_sessions,
                "moderate_sessions": moderate_sessions,
                "long_sessions": long_sessions,
                "very_long_sessions": very_long_sessions
            },
            "outlier_analysis": {
                "records_with_outliers": len([s for s in response_data["session_analysis"] 
                                            if s["distribution_analysis"]["median_to_average_ratio"] < 0.7]),
                "consistent_patterns": len([s for s in response_data["session_analysis"] 
                                          if 0.8 <= s["distribution_analysis"]["median_to_average_ratio"] <= 1.2])
            },
            "engagement_insights": {
                "high_engagement_users": len([s for s in response_data["session_analysis"] 
                                            if s["session_statistics"]["median_session_minutes"] > 30]),
                "quick_usage_users": len([s for s in response_data["session_analysis"] 
                                        if s["session_statistics"]["median_session_minutes"] < 5]),
                "median_vs_average_correlation": round(overall_avg_median / overall_avg_average, 2) if overall_avg_average > 0 else 0
            }
        }
        
        # Add top performers
        response_data["top_performers"] = {
            "longest_median_sessions": [
                {
                    "user": s["user"],
                    "app": s["application_name"],
                    "median_minutes": s["session_statistics"]["median_session_minutes"],
                    "total_sessions": s["session_statistics"]["total_sessions"]
                }
                for s in sorted(response_data["session_analysis"], 
                              key=lambda x: x["session_statistics"]["median_session_minutes"], reverse=True)
            ][:10],
            "most_consistent_users": [
                {
                    "user": s["user"],
                    "app": s["application_name"],
                    "consistency_ratio": s["distribution_analysis"]["median_to_average_ratio"],
                    "median_minutes": s["session_statistics"]["median_session_minutes"]
                }
                for s in sorted(response_data["session_analysis"], 
                              key=lambda x: abs(x["distribution_analysis"]["median_to_average_ratio"] - 1.0))
            ][:10]
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Median session length analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} records, {overall_avg_median:.1f}min avg median")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in median_session_length: {e}")
        if ctx:
            ctx.error(f"Failed to calculate median session lengths: {e}")
        
        return {
            "tool": "median_session_length",
            "error": str(e),
            "message": "Failed to calculate median session lengths"
        }
