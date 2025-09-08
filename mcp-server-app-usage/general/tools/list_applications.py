"""
Tool: List Applications
Category: General
Feature ID: 1

Description:
    List all applications being tracked in the system. This tool provides
    a comprehensive view of all applications in the app_list table with
    optional filtering and sorting capabilities.

Parameters:
    - limit (int, optional): Maximum number of applications to return (default: 100)
    - app_type (str, optional): Filter by application type
    - enable_tracking (bool, optional): Filter by tracking status
    - sort_by (str, optional): Sort field (name, type, released_date, publisher)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with application list and metadata

Examples:
    Basic usage:
    Input: {}
    Output: List of all tracked applications

    Filtered usage:
    Input: {"app_type": "productivity", "limit": 10}
    Output: Top 10 productivity applications

Database Tables Used:
    - app_list: For application metadata

Related Tools:
    - app_details: Get detailed information about a specific application
    - tracking_status: Check tracking configuration for applications

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
async def list_applications(
    limit: int = 100,
    app_type: Optional[str] = None,
    enable_tracking: Optional[bool] = None,
    sort_by: str = "app_name",
    sort_order: str = "asc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List all applications being tracked in the system with optional filtering and sorting.
    
    Args:
        limit: Maximum number of applications to return (default: 100, max: 1000)
        app_type: Filter by application type (e.g., 'productivity', 'entertainment', 'development')
        enable_tracking: Filter by tracking status (true for enabled, false for disabled)
        sort_by: Field to sort by (app_name, app_type, released_date, publisher, registered_date)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing application list and metadata
    """
    try:
        if ctx:
            ctx.info(f"Listing applications with limit: {limit}, filters: app_type={app_type}, tracking={enable_tracking}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['app_name', 'app_type', 'released_date', 'publisher', 'registered_date']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Build filters
        filters = {}
        if app_type:
            filters['app_type'] = app_type
        if enable_tracking is not None:
            filters['enable_tracking'] = enable_tracking
        
        # Build query
        base_query = """
        SELECT 
            app_id,
            app_name,
            app_type,
            current_version,
            released_date,
            publisher,
            description,
            download_link,
            enable_tracking,
            track_usage,
            track_location,
            track_cm,
            track_intr,
            registered_date
        FROM app_list
        """
        
        order_clause = f"{sort_by} {sort_order.upper()}"
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by=order_clause,
            limit=limit
        )
        
        if ctx:
            ctx.debug(f"Executing query: {query}")
        
        # Execute query
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
        
        # Format response
        response_data = {
            "tool": "list_applications",
            "description": "List of all tracked applications",
            "total_applications": result.total_count,
            "query_time_ms": result.query_time_ms,
            "filters_applied": {
                "app_type": app_type,
                "enable_tracking": enable_tracking,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "applications": []
        }
        
        # Process applications
        for app in result.data:
            app_info = {
                "app_id": app["app_id"],
                "name": app["app_name"],
                "type": app["app_type"],
                "version": app["current_version"],
                "released_date": app["released_date"],
                "publisher": app["publisher"],
                "description": app["description"][:100] + "..." if len(app["description"]) > 100 else app["description"],
                "download_link": app["download_link"],
                "tracking": {
                    "enabled": bool(app["enable_tracking"]),
                    "usage": bool(app["track_usage"]),
                    "location": bool(app["track_location"]),
                    "cpu_memory": bool(app["track_cm"]),
                    "interval_seconds": app["track_intr"]
                },
                "registered_date": app["registered_date"]
            }
            response_data["applications"].append(app_info)
        
        # Add summary statistics
        if result.data:
            app_types = {}
            publishers = {}
            tracking_enabled = 0
            
            for app in result.data:
                # Count by type
                app_type_key = app["app_type"]
                app_types[app_type_key] = app_types.get(app_type_key, 0) + 1
                
                # Count by publisher
                publisher_key = app["publisher"]
                publishers[publisher_key] = publishers.get(publisher_key, 0) + 1
                
                # Count tracking enabled
                if app["enable_tracking"]:
                    tracking_enabled += 1
            
            response_data["summary"] = {
                "total_applications": len(result.data),
                "tracking_enabled": tracking_enabled,
                "tracking_disabled": len(result.data) - tracking_enabled,
                "unique_app_types": len(app_types),
                "unique_publishers": len(publishers),
                "top_app_types": sorted(app_types.items(), key=lambda x: x[1], reverse=True)[:5],
                "top_publishers": sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        if ctx:
            ctx.info("Successfully processed application list")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in list_applications: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve application list: {e}")
        
        error_response = {
            "tool": "list_applications",
            "error": str(e),
            "message": "Failed to retrieve application list"
        }
        return error_response
