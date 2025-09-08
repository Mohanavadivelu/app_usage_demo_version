"""
Tool: App Users
Category: User Centric
Feature ID: 21

Description:
    List users who have used a specific application

Parameters:
    - application_name (str, required): Application name, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - limit (int, optional): Maximum number of results

Returns:
    - List users who have used a specific application with detailed analytics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query
from shared.analytics_utils import format_duration, rank_results, calculate_percentages

logger = logging.getLogger(__name__)


async def app_users_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the app_users tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['application_name'],
            optional=['start_date', 'end_date', 'limit']
        )
        
        application_name = validated_params.get('application_name')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Execute main query
        query = """
            SELECT 
        user,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as session_count,
        AVG(duration_seconds) as avg_session_seconds,
        MIN(log_date) as first_usage,
        MAX(log_date) as last_usage,
        COUNT(DISTINCT platform) as platforms_used
            FROM app_usage
            WHERE application_name = ?
            GROUP BY user
            ORDER BY total_seconds DESC
            """
        params = (application_name,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "app_users",
            "description": "List users who have used a specific application",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "user": record.get("user"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "session_count": record.get("session_count"),
                "avg_session_minutes": round(record.get("avg_session_seconds", 0) / 60, 2),
                "first_usage": record.get("first_usage"),
                "last_usage": record.get("last_usage"),
                "platforms_used": record.get("platforms_used"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in app_users_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "app_users",
                "error": str(e),
                "message": "Failed to execute app_users"
            }, indent=2)
        )]


app_users_tool = Tool(
    name="app_users",
    description="List users who have used a specific application",
    inputSchema={
        "type": "object",
        "properties": {
            "application_name": {
                "type": "string",
                "description": "Application name to analyze"
        },
        "start_date": {
                "type": "string",
                "description": "Start Date for analysis (YYYY-MM-DD format)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "end_date": {
                "type": "string",
                "description": "End Date for analysis (YYYY-MM-DD format)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
        }
        },
        "required": ["application_name"],
        "additionalProperties": False
    }
)

app_users_tool.handler = app_users_handler
