"""
Tool: Tracking Status
Category: General
Feature ID: 3

Description:
    Identify which applications have tracking enabled or disabled.
    Provides filtering and summary statistics for tracking configuration.

Parameters:
    - tracking_enabled (bool, optional): Filter by tracking status
    - limit (int, optional): Maximum number of results

Returns:
    - List of applications with their tracking status

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, validate_parameters, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from main module
import sys
main_module = sys.modules.get('__main__')
if main_module and hasattr(main_module, 'mcp'):
    mcp = main_module.mcp
else:
    # Fallback for when imported from other contexts
    from main import mcp


@mcp.tool()
async def tracking_status(
    tracking_enabled: Optional[bool] = None,
    limit: int = 100,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Check which applications have tracking enabled or disabled.
    
    Args:
        tracking_enabled: Filter by tracking status (true for enabled, false for disabled)
        limit: Maximum number of applications to return (default: 100, max: 1000)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing applications with their tracking status
    """
    try:
        if ctx:
            filter_desc = f"tracking_enabled={tracking_enabled}" if tracking_enabled is not None else "all applications"
            ctx.info(f"Checking tracking status for {filter_desc}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        # Build query
        base_query = """
        SELECT 
            app_name, app_type, publisher, enable_tracking,
            track_usage, track_location, track_cm, track_intr
        FROM app_list
        """
        
        filters = {}
        if tracking_enabled is not None:
            filters['enable_tracking'] = tracking_enabled
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by="app_name ASC",
            limit=limit
        )
        
        if ctx:
            ctx.debug(f"Executing tracking status query with filters: {filters}")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
        
        # Process results
        response_data = {
            "tool": "tracking_status",
            "description": "Application tracking status overview",
            "query_time_ms": result.query_time_ms,
            "total_applications": result.total_count,
            "filter_applied": {
                "tracking_enabled": tracking_enabled,
                "limit": limit
            },
            "applications": []
        }
        
        enabled_count = 0
        disabled_count = 0
        
        for app in result.data:
            app_info = {
                "name": app["app_name"],
                "type": app["app_type"],
                "publisher": app["publisher"],
                "tracking": {
                    "enabled": bool(app["enable_tracking"]),
                    "usage": bool(app["track_usage"]),
                    "location": bool(app["track_location"]),
                    "cpu_memory": bool(app["track_cm"]),
                    "interval_seconds": app["track_intr"]
                }
            }
            response_data["applications"].append(app_info)
            
            if app["enable_tracking"]:
                enabled_count += 1
            else:
                disabled_count += 1
        
        response_data["summary"] = {
            "tracking_enabled": enabled_count,
            "tracking_disabled": disabled_count,
            "percentage_enabled": round((enabled_count / len(result.data) * 100), 2) if result.data else 0
        }
        
        if ctx:
            ctx.info(f"Summary: {enabled_count} enabled, {disabled_count} disabled ({response_data['summary']['percentage_enabled']}% enabled)")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in tracking_status: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve tracking status: {e}")
        
        return {
            "tool": "tracking_status",
            "error": str(e),
            "message": "Failed to retrieve tracking status"
        }
