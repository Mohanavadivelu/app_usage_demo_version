"""
Tool: App Details
Category: General
Feature ID: 2

Description:
    Show detailed information about a specific application including metadata,
    tracking configuration, and usage statistics summary.

Parameters:
    - app_name (str, required): Name of the application to get details for
    - include_usage_stats (bool, optional): Include usage statistics summary

Returns:
    - Detailed application information with optional usage statistics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query

logger = logging.getLogger(__name__)

# Import the mcp instance from main module
from main import mcp


@mcp.tool()
async def app_details(
    app_name: str,
    include_usage_stats: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific application.
    
    Args:
        app_name: Name of the application to get details for
        include_usage_stats: Include usage statistics summary (default: false)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing detailed application information
    """
    try:
        if ctx:
            ctx.info(f"Getting details for application: {app_name}")
        
        # Get app details from app_list
        app_query = """
        SELECT * FROM app_list WHERE app_name = ?
        """
        
        if ctx:
            ctx.debug(f"Executing app details query for: {app_name}")
        
        app_result = execute_analytics_query(app_query, (app_name,))
        
        if not app_result.data:
            if ctx:
                ctx.warning(f"Application '{app_name}' not found")
            return {
                "tool": "app_details",
                "error": f"Application '{app_name}' not found",
                "message": "No application found with the specified name"
            }
        
        app_data = app_result.data[0]
        
        if ctx:
            ctx.info(f"Found application: {app_data['app_name']} (ID: {app_data['app_id']})")
        
        # Build response
        response_data = {
            "tool": "app_details",
            "query_time_ms": app_result.query_time_ms,
            "application": {
                "app_id": app_data["app_id"],
                "name": app_data["app_name"],
                "type": app_data["app_type"],
                "current_version": app_data["current_version"],
                "released_date": app_data["released_date"],
                "publisher": app_data["publisher"],
                "description": app_data["description"],
                "download_link": app_data["download_link"],
                "registered_date": app_data["registered_date"],
                "tracking_configuration": {
                    "enabled": bool(app_data["enable_tracking"]),
                    "usage_tracking": bool(app_data["track_usage"]),
                    "location_tracking": bool(app_data["track_location"]),
                    "cpu_memory_tracking": bool(app_data["track_cm"]),
                    "tracking_interval_seconds": app_data["track_intr"]
                }
            }
        }
        
        # Add usage statistics if requested
        if include_usage_stats:
            if ctx:
                ctx.info("Including usage statistics")
                ctx.report_progress(50, 100, "Fetching usage statistics...")
            
            usage_query = """
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(DISTINCT user) as unique_users,
                SUM(duration_seconds) as total_seconds,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(log_date) as first_usage_date,
                MAX(log_date) as last_usage_date,
                COUNT(DISTINCT platform) as platforms_used
            FROM app_usage 
            WHERE application_name = ?
            """
            usage_result = execute_analytics_query(usage_query, (app_name,))
            
            if usage_result.data and usage_result.data[0]['total_sessions'] > 0:
                usage_stats = usage_result.data[0]
                response_data["usage_statistics"] = {
                    "total_sessions": usage_stats["total_sessions"],
                    "unique_users": usage_stats["unique_users"],
                    "total_usage_hours": round(usage_stats["total_seconds"] / 3600, 2),
                    "average_session_minutes": round(usage_stats["avg_session_seconds"] / 60, 2),
                    "first_usage_date": usage_stats["first_usage_date"],
                    "last_usage_date": usage_stats["last_usage_date"],
                    "platforms_used": usage_stats["platforms_used"]
                }
                if ctx:
                    ctx.info(f"Found {usage_stats['total_sessions']} sessions from {usage_stats['unique_users']} users")
            else:
                response_data["usage_statistics"] = {
                    "message": "No usage data found for this application"
                }
                if ctx:
                    ctx.info("No usage data found for this application")
        
        if ctx:
            ctx.report_progress(100, 100, "Application details retrieved successfully")
            ctx.info("Successfully retrieved application details")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in app_details: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve application details: {e}")
        
        return {
            "tool": "app_details",
            "error": str(e),
            "message": "Failed to retrieve application details"
        }
