"""
Tool: Recent Releases
Category: General
Feature ID: 5

Description:
    List applications released in the last X days or months.

Parameters:
    - days (int, optional): Number of days to look back
    - months (int, optional): Number of months to look back
    - limit (int, optional): Maximum number of results

Returns:
    - List of recently released applications

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging
from datetime import datetime, timedelta

from shared.database_utils import execute_analytics_query, validate_parameters
from shared.date_utils import days_ago, format_date

logger = logging.getLogger(__name__)


async def recent_releases_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the recent_releases tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=[],
            optional=['days', 'months', 'limit']
        )
        
        days = validated_params.get('days')
        months = validated_params.get('months')
        limit = validated_params.get('limit', 100)
        
        # Calculate cutoff date
        if days:
            cutoff_date = days_ago(days)
        elif months:
            cutoff_date = days_ago(months * 30)  # Approximate
        else:
            cutoff_date = days_ago(30)  # Default to 30 days
        
        query = """
        SELECT 
            app_name, app_type, current_version, released_date,
            publisher, description, enable_tracking
        FROM app_list
        WHERE released_date >= ?
        ORDER BY released_date DESC
        LIMIT ?
        """
        
        result = execute_analytics_query(query, (cutoff_date, limit))
        
        response_data = {
            "tool": "recent_releases",
            "description": f"Applications released since {cutoff_date}",
            "cutoff_date": cutoff_date,
            "total_recent_releases": result.total_count,
            "recent_applications": []
        }
        
        publishers = {}
        app_types = {}
        
        for app in result.data:
            app_info = {
                "name": app["app_name"],
                "type": app["app_type"],
                "version": app["current_version"],
                "released_date": app["released_date"],
                "publisher": app["publisher"],
                "description": app["description"][:100] + "..." if len(app["description"]) > 100 else app["description"],
                "tracking_enabled": bool(app["enable_tracking"])
            }
            response_data["recent_applications"].append(app_info)
            
            # Count by publisher and type
            publishers[app["publisher"]] = publishers.get(app["publisher"], 0) + 1
            app_types[app["app_type"]] = app_types.get(app["app_type"], 0) + 1
        
        response_data["summary"] = {
            "total_releases": len(result.data),
            "top_publishers": sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:5],
            "app_types": sorted(app_types.items(), key=lambda x: x[1], reverse=True)
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in recent_releases_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "recent_releases",
                "error": str(e),
                "message": "Failed to retrieve recent releases"
            }, indent=2)
        )]


recent_releases_tool = Tool(
    name="recent_releases",
    description="List applications released in the last X days or months",
    inputSchema={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to look back",
                "minimum": 1,
                "maximum": 365
            },
            "months": {
                "type": "integer",
                "description": "Number of months to look back",
                "minimum": 1,
                "maximum": 12
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

recent_releases_tool.handler = recent_releases_handler
