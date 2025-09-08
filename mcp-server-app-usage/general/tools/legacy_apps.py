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

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters

logger = logging.getLogger(__name__)


async def legacy_apps_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the legacy_apps tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=[],
            optional=['limit']
        )
        
        limit = validated_params.get('limit', 100)
        
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
        
        result = execute_analytics_query(query, (limit,))
        
        response_data = {
            "tool": "legacy_apps",
            "description": "Legacy applications analysis",
            "total_legacy_apps": result.total_count,
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
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in legacy_apps_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "legacy_apps",
                "error": str(e),
                "message": "Failed to retrieve legacy applications"
            }, indent=2)
        )]


legacy_apps_tool = Tool(
    name="legacy_apps",
    description="List legacy applications with usage statistics",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of legacy apps to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            }
        },
        "additionalProperties": False
    }
)

legacy_apps_tool.handler = legacy_apps_handler
