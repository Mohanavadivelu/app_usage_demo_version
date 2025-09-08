"""
Tool: Top Publishers
Category: General
Feature ID: 6

Description:
    Show publishers who have released the most applications.

Parameters:
    - top_n (int, optional): Number of top publishers to return
    - include_app_details (bool, optional): Include list of apps per publisher

Returns:
    - Ranked list of publishers by application count

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters

logger = logging.getLogger(__name__)


async def top_publishers_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the top_publishers tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=[],
            optional=['top_n', 'include_app_details']
        )
        
        top_n = validated_params.get('top_n', 10)
        include_app_details = validated_params.get('include_app_details', False)
        
        # Get publisher rankings
        query = """
        SELECT 
            publisher,
            COUNT(*) as app_count,
            COUNT(CASE WHEN enable_tracking = 1 THEN 1 END) as tracking_enabled_count,
            GROUP_CONCAT(DISTINCT app_type) as app_types
        FROM app_list
        GROUP BY publisher
        ORDER BY app_count DESC
        LIMIT ?
        """
        
        result = execute_analytics_query(query, (top_n,))
        
        response_data = {
            "tool": "top_publishers",
            "description": f"Top {top_n} publishers by application count",
            "total_publishers": result.total_count,
            "publishers": []
        }
        
        for i, publisher in enumerate(result.data, 1):
            publisher_info = {
                "rank": i,
                "publisher": publisher["publisher"],
                "total_applications": publisher["app_count"],
                "tracking_enabled": publisher["tracking_enabled_count"],
                "tracking_disabled": publisher["app_count"] - publisher["tracking_enabled_count"],
                "app_types": publisher["app_types"].split(",") if publisher["app_types"] else []
            }
            
            # Add app details if requested
            if include_app_details:
                app_query = """
                SELECT app_name, app_type, current_version, released_date, enable_tracking
                FROM app_list
                WHERE publisher = ?
                ORDER BY released_date DESC
                """
                app_result = execute_analytics_query(app_query, (publisher["publisher"],))
                publisher_info["applications"] = [
                    {
                        "name": app["app_name"],
                        "type": app["app_type"],
                        "version": app["current_version"],
                        "released_date": app["released_date"],
                        "tracking_enabled": bool(app["enable_tracking"])
                    }
                    for app in app_result.data
                ]
            
            response_data["publishers"].append(publisher_info)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in top_publishers_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "top_publishers",
                "error": str(e),
                "message": "Failed to retrieve top publishers"
            }, indent=2)
        )]


top_publishers_tool = Tool(
    name="top_publishers",
    description="Show publishers who have released the most applications",
    inputSchema={
        "type": "object",
        "properties": {
            "top_n": {
                "type": "integer",
                "description": "Number of top publishers to return (default: 10)",
                "minimum": 1,
                "maximum": 100,
                "default": 10
            },
            "include_app_details": {
                "type": "boolean",
                "description": "Include list of applications per publisher (default: false)",
                "default": False
            }
        },
        "additionalProperties": False
    }
)

top_publishers_tool.handler = top_publishers_handler
