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

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query

logger = logging.getLogger(__name__)


async def app_versions_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the app_versions tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=[],
            optional=['limit', 'sort_by', 'sort_order']
        )
        
        limit = validated_params.get('limit', 100)
        sort_by = validated_params.get('sort_by', 'app_name')
        sort_order = validated_params.get('sort_order', 'asc')
        
        # Validate sort parameters
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
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "app_versions",
            "description": "Applications with version information",
            "total_applications": result.total_count,
            "applications": []
        }
        
        version_stats = {}
        publisher_versions = {}
        
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
            
            # Collect version statistics
            version = app["current_version"]
            version_stats[version] = version_stats.get(version, 0) + 1
            
            publisher = app["publisher"]
            if publisher not in publisher_versions:
                publisher_versions[publisher] = set()
            publisher_versions[publisher].add(version)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_applications": len(result.data),
            "unique_versions": len(version_stats),
            "most_common_versions": sorted(version_stats.items(), key=lambda x: x[1], reverse=True)[:5],
            "publishers_with_most_versions": [
                {"publisher": pub, "version_count": len(versions)}
                for pub, versions in sorted(publisher_versions.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            ]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in app_versions_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "app_versions",
                "error": str(e),
                "message": "Failed to retrieve application versions"
            }, indent=2)
        )]


app_versions_tool = Tool(
    name="app_versions",
    description="List applications along with their current versions",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of applications to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            },
            "sort_by": {
                "type": "string",
                "description": "Field to sort by",
                "enum": ["app_name", "current_version", "released_date"],
                "default": "app_name"
            },
            "sort_order": {
                "type": "string",
                "description": "Sort order",
                "enum": ["asc", "desc"],
                "default": "asc"
            }
        },
        "additionalProperties": False
    }
)

app_versions_tool.handler = app_versions_handler
