"""
Tool: Usage Time Stats
Category: Usage Statistics
Feature ID: 8

Description:
    List applications and their total usage time in hours.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD)
    - limit (int, optional): Maximum number of applications to return

Returns:
    - List of applications with total usage time in hours

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query
from shared.analytics_utils import format_duration

logger = logging.getLogger(__name__)


async def usage_time_stats_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the usage_time_stats tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'start_date', 'end_date', 'limit'}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Build query with optional date filters
        base_query = """
        SELECT 
            application_name,
            SUM(duration_seconds) as total_seconds,
            COUNT(*) as total_sessions,
            COUNT(DISTINCT user) as unique_users,
            AVG(duration_seconds) as avg_session_seconds
        FROM app_usage
        """
        
        filters = {}
        if start_date:
            filters['log_date'] = (start_date, end_date) if end_date else (start_date, '9999-12-31')
        elif end_date:
            filters['log_date'] = ('1900-01-01', end_date)
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="application_name",
            order_by="total_seconds DESC",
            limit=limit
        )
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "usage_time_stats",
            "description": "Application usage time statistics",
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "total_applications": result.total_count,
            "applications": []
        }
        
        total_usage_seconds = 0
        
        for app in result.data:
            usage_hours = app["total_seconds"] / 3600
            total_usage_seconds += app["total_seconds"]
            
            app_info = {
                "application_name": app["application_name"],
                "total_usage_hours": round(usage_hours, 2),
                "total_usage_formatted": format_duration(app["total_seconds"], "human"),
                "total_sessions": app["total_sessions"],
                "unique_users": app["unique_users"],
                "average_session_minutes": round(app["avg_session_seconds"] / 60, 2)
            }
            response_data["applications"].append(app_info)
        
        response_data["summary"] = {
            "total_usage_hours": round(total_usage_seconds / 3600, 2),
            "total_usage_formatted": format_duration(total_usage_seconds, "human"),
            "applications_analyzed": len(result.data)
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in usage_time_stats_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "usage_time_stats",
                "error": str(e),
                "message": "Failed to retrieve usage time statistics"
            }, indent=2)
        )]


usage_time_stats_tool = Tool(
    name="usage_time_stats",
    description="List applications and their total usage time in hours",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date for analysis (YYYY-MM-DD format)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "end_date": {
                "type": "string",
                "description": "End date for analysis (YYYY-MM-DD format)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
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

usage_time_stats_tool.handler = usage_time_stats_handler
