"""
Tool: Legacy Apps
Category: General
Feature ID: 4

Description:
    List legacy applications based on the legacy_app flag in the usage data.

Parameters:
    - limit (int, optional): Maximum number of results

Returns:
    - List of legacy applications with usage statistics

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
async def legacy_apps(
    limit: int = 100,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List legacy applications with usage statistics.
    
    Args:
        limit: Maximum number of legacy apps to return (default: 100, max: 1000)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing legacy applications with usage statistics
    """
    try:
        if ctx:
            ctx.info(f"Retrieving legacy applications, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        # Get legacy apps from usage data
        query = """
        SELECT 
            u.application_name,
            u.application_version,
            COUNT(*) as usage_sessions,
            COUNT(DISTINCT u.user) as unique_users,
            SUM(u.duration_seconds) as total_seconds,
            MAX(u.log_date) as last_used_date,
            l.app_type,
            l.publisher
        FROM app_usage u
        LEFT JOIN app_list l ON u.application_name = l.app_name
        WHERE u.legacy_app = 1
        GROUP BY u.application_name, u.application_version
        ORDER BY total_seconds DESC
        LIMIT ?
        """
        
        if ctx:
            ctx.debug("Executing legacy apps query")
            ctx.report_progress(25, 100, "Querying legacy applications...")
        
        result = execute_analytics_query(query, (limit,))
        
        if ctx:
            ctx.info(f"Found {len(result.data)} legacy applications in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing legacy app data...")
        
        response_data = {
            "tool": "legacy_apps",
            "description": "Legacy applications analysis",
            "query_time_ms": result.query_time_ms,
            "total_legacy_apps": result.total_count,
            "limit_applied": limit,
            "legacy_applications": []
        }
        
        total_usage_hours = 0
        total_users = set()
        
        for app in result.data:
            usage_hours = app["total_seconds"] / 3600
            total_usage_hours += usage_hours
            
            app_info = {
                "name": app["application_name"],
                "version": app["application_version"],
                "type": app["app_type"] or "Unknown",
                "publisher": app["publisher"] or "Unknown",
                "usage_sessions": app["usage_sessions"],
                "unique_users": app["unique_users"],
                "total_usage_hours": round(usage_hours, 2),
                "last_used_date": app["last_used_date"]
            }
            response_data["legacy_applications"].append(app_info)
        
        response_data["summary"] = {
            "total_legacy_apps": len(result.data),
            "total_usage_hours": round(total_usage_hours, 2),
            "average_usage_per_app": round(total_usage_hours / len(result.data), 2) if result.data else 0
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Legacy apps analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} legacy apps, {response_data['summary']['total_usage_hours']} total hours")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in legacy_apps: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve legacy applications: {e}")
        
        return {
            "tool": "legacy_apps",
            "error": str(e),
            "message": "Failed to retrieve legacy applications"
        }
