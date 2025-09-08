"""
Tool: App Versions
Category: General
Feature ID: 7

Description:
    List applications along with their current versions.

Parameters:
    - limit (int, optional): Maximum number of applications to return
    - sort_by (str, optional): Sort field (name, version, released_date)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - List of applications with version information

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from main module
from main import mcp


@mcp.tool()
async def app_versions(
    limit: int = 100,
    sort_by: str = "app_name",
    sort_order: str = "asc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List applications along with their current versions.
    
    Args:
        limit: Maximum number of applications to return (default: 100, max: 1000)
        sort_by: Field to sort by (app_name, current_version, released_date)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing applications with version information
    """
    try:
        if ctx:
            ctx.info(f"Listing app versions, limit: {limit}, sort: {sort_by} {sort_order}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['app_name', 'current_version', 'released_date']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Build query
        base_query = """
        SELECT 
            app_name, app_type, current_version, released_date,
            publisher, enable_tracking
        FROM app_list
        """
        
        order_clause = f"{sort_by} {sort_order.upper()}"
        query, params = build_query(
            base_query=base_query,
            order_by=order_clause,
            limit=limit
        )
        
        if ctx:
            ctx.debug(f"Executing app versions query with sort: {order_clause}")
            ctx.report_progress(25, 100, "Querying application versions...")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing version data...")
        
        response_data = {
            "tool": "app_versions",
            "description": "Applications with version information",
            "query_time_ms": result.query_time_ms,
            "total_applications": result.total_count,
            "sort_applied": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "limit": limit
            },
            "applications": []
        }
        
        version_stats = {}
        publisher_versions = {}
        tracking_enabled_count = 0
        
        for app in result.data:
            app_info = {
                "name": app["app_name"],
                "type": app["app_type"],
                "current_version": app["current_version"],
                "released_date": app["released_date"],
                "publisher": app["publisher"],
                "tracking_enabled": bool(app["enable_tracking"])
            }
            response_data["applications"].append(app_info)
            
            # Collect statistics
            version = app["current_version"]
            version_stats[version] = version_stats.get(version, 0) + 1
            
            publisher = app["publisher"]
            if publisher not in publisher_versions:
                publisher_versions[publisher] = set()
            publisher_versions[publisher].add(version)
            
            if app["enable_tracking"]:
                tracking_enabled_count += 1
        
        # Add summary statistics
        response_data["summary"] = {
            "total_applications": len(result.data),
            "unique_versions": len(version_stats),
            "tracking_enabled": tracking_enabled_count,
            "tracking_disabled": len(result.data) - tracking_enabled_count,
            "tracking_percentage": round((tracking_enabled_count / len(result.data) * 100), 2) if result.data else 0,
            "most_common_versions": sorted(version_stats.items(), key=lambda x: x[1], reverse=True)[:5],
            "publishers_with_most_versions": [
                {"publisher": pub, "version_count": len(versions)}
                for pub, versions in sorted(publisher_versions.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            ]
        }
        
        if ctx:
            ctx.report_progress(100, 100, "App versions analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} apps, {len(version_stats)} unique versions")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in app_versions: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve application versions: {e}")
        
        return {
            "tool": "app_versions",
            "error": str(e),
            "message": "Failed to retrieve application versions"
        }
