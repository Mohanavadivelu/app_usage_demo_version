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

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query

logger = logging.getLogger(__name__)


async def tracking_status_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the tracking_status tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=[],
            optional=['tracking_enabled', 'limit']
        )
        
        tracking_enabled = validated_params.get('tracking_enabled')
        limit = validated_params.get('limit', 100)
        
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
        
        result = execute_analytics_query(query, params)
        
        # Process results
        response_data = {
            "tool": "tracking_status",
            "description": "Application tracking status overview",
            "total_applications": result.total_count,
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
            "percentage_enabled": round((enabled_count / result.total_count * 100), 2) if result.total_count > 0 else 0
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in tracking_status_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "tracking_status",
                "error": str(e),
                "message": "Failed to retrieve tracking status"
            }, indent=2)
        )]


tracking_status_tool = Tool(
    name="tracking_status",
    description="Check which applications have tracking enabled or disabled",
    inputSchema={
        "type": "object",
        "properties": {
            "tracking_enabled": {
                "type": "boolean",
                "description": "Filter by tracking status (true for enabled, false for disabled)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of applications to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            }
        },
        "additionalProperties": False
    }
)

tracking_status_tool.handler = tracking_status_handler
