"""
Tool: Version Usage Breakdown
Category: Version Tracking
Feature ID: 33

Description:
    Usage statistics by application version. This tool provides detailed
    analytics on how different versions of applications are being used,
    including session counts, duration, and user engagement metrics.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - sort_by (str, optional): Sort field (usage_sessions, total_hours, unique_users)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with version usage statistics and analytics

Examples:
    Basic usage:
    Input: {}
    Output: Usage breakdown for all application versions

    Filtered usage:
    Input: {"app_name": "Chrome", "limit": 10}
    Output: Top 10 Chrome version usage statistics

Database Tables Used:
    - app_usage: For usage statistics by version
    - app_list: For application metadata

Related Tools:
    - legacy_vs_modern: Compare legacy vs modern versions
    - version_distribution: Analyze version distribution patterns

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
async def version_usage_breakdown(
    limit: int = 100,
    app_name: Optional[str] = None,
    sort_by: str = "usage_sessions",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Get usage statistics by application version.
    
    Args:
        limit: Maximum number of results to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        sort_by: Field to sort by (usage_sessions, total_hours, unique_users, avg_session_minutes)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing version usage statistics and analytics
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing version usage breakdown {filter_desc}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['usage_sessions', 'total_hours', 'unique_users', 'avg_session_minutes']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Build query for version usage statistics
        base_query = """
        SELECT 
            u.application_name,
            u.application_version,
            COUNT(*) as usage_sessions,
            COUNT(DISTINCT u.user) as unique_users,
            SUM(u.duration_seconds) as total_seconds,
            AVG(u.duration_seconds) as avg_session_seconds,
            MIN(u.log_date) as first_usage_date,
            MAX(u.log_date) as last_usage_date,
            l.app_type,
            l.publisher,
            l.current_version,
            CASE WHEN u.application_version = l.current_version THEN 1 ELSE 0 END as is_current_version
        FROM app_usage u
        LEFT JOIN app_list l ON u.application_name = l.app_name
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['u.application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'usage_sessions': 'usage_sessions',
            'total_hours': 'total_seconds',
            'unique_users': 'unique_users',
            'avg_session_minutes': 'avg_session_seconds'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="u.application_name, u.application_version",
            order_by=order_clause,
            limit=limit
        )
        
        if ctx:
            ctx.debug(f"Executing version usage breakdown query")
            ctx.report_progress(25, 100, "Querying version usage data...")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} version records in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing version usage statistics...")
        
        # Format response
        response_data = {
            "tool": "version_usage_breakdown",
            "description": "Usage statistics by application version",
            "query_time_ms": result.query_time_ms,
            "total_version_records": result.total_count,
            "filters_applied": {
                "app_name": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "version_usage": []
        }
        
        # Process version usage data
        total_sessions = 0
        total_hours = 0
        unique_apps = set()
        current_version_usage = 0
        outdated_version_usage = 0
        
        for record in result.data:
            total_seconds = record["total_seconds"] or 0
            total_hours_for_version = total_seconds / 3600
            avg_session_minutes = (record["avg_session_seconds"] or 0) / 60
            
            total_sessions += record["usage_sessions"]
            total_hours += total_hours_for_version
            unique_apps.add(record["application_name"])
            
            if record["is_current_version"]:
                current_version_usage += record["usage_sessions"]
            else:
                outdated_version_usage += record["usage_sessions"]
            
            version_info = {
                "application_name": record["application_name"],
                "version": record["application_version"],
                "app_type": record["app_type"],
                "publisher": record["publisher"],
                "is_current_version": bool(record["is_current_version"]),
                "current_version": record["current_version"],
                "usage_statistics": {
                    "sessions": record["usage_sessions"],
                    "unique_users": record["unique_users"],
                    "total_hours": round(total_hours_for_version, 2),
                    "average_session_minutes": round(avg_session_minutes, 2),
                    "first_usage_date": record["first_usage_date"],
                    "last_usage_date": record["last_usage_date"]
                }
            }
            response_data["version_usage"].append(version_info)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_sessions": total_sessions,
            "total_usage_hours": round(total_hours, 2),
            "unique_applications": len(unique_apps),
            "version_records_analyzed": len(result.data),
            "current_version_sessions": current_version_usage,
            "outdated_version_sessions": outdated_version_usage,
            "outdated_usage_percentage": round((outdated_version_usage / total_sessions * 100), 2) if total_sessions > 0 else 0
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Version usage breakdown analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} versions, {total_sessions} total sessions")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in version_usage_breakdown: {e}")
        if ctx:
            ctx.error(f"Failed to analyze version usage breakdown: {e}")
        
        return {
            "tool": "version_usage_breakdown",
            "error": str(e),
            "message": "Failed to analyze version usage breakdown"
        }
