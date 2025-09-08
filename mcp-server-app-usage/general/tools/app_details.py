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

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query
from shared.models import AnalyticsResult

logger = logging.getLogger(__name__)


async def app_details_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the app_details tool request."""
    try:
        # Validate parameters
        validated_params = validate_parameters(
            arguments,
            required=['app_name'],
            optional=['include_usage_stats']
        )
        
        app_name = validated_params['app_name']
        include_usage_stats = validated_params.get('include_usage_stats', False)
        
        # Get app details from app_list
        app_query = """
        SELECT * FROM app_list WHERE app_name = ?
        """
        app_result = execute_analytics_query(app_query, (app_name,))
        
        if not app_result.data:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "tool": "app_details",
                    "error": f"Application '{app_name}' not found",
                    "message": "No application found with the specified name"
                }, indent=2)
            )]
        
        app_data = app_result.data[0]
        
        # Build response
        response_data = {
            "tool": "app_details",
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
            else:
                response_data["usage_statistics"] = {
                    "message": "No usage data found for this application"
                }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in app_details_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "app_details",
                "error": str(e),
                "message": "Failed to retrieve application details"
            }, indent=2)
        )]


# Define the MCP tool
app_details_tool = Tool(
    name="app_details",
    description="Get detailed information about a specific application",
    inputSchema={
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the application to get details for"
            },
            "include_usage_stats": {
                "type": "boolean",
                "description": "Include usage statistics summary (default: false)",
                "default": False
            }
        },
        "required": ["app_name"],
        "additionalProperties": False
    }
)

app_details_tool.handler = app_details_handler
