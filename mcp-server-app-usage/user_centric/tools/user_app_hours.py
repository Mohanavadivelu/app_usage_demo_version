"""
Tool: User App Hours
Category: User Centric
Feature ID: 17

Description:
    Hours spent by user on specific application

Parameters:
    - user (str, required): User identifier, - application_name (str, required): Application name, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis

Returns:
    - Hours spent by user on specific application with detailed analytics

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


async def user_app_hours_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_app_hours tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['user', 'application_name'],
            optional=['start_date', 'end_date']
        )
        
        user = validated_params.get('user')
        application_name = validated_params.get('application_name')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        
        # Execute main query
        query = """
            SELECT 
        user,
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as session_count,
        AVG(duration_seconds) as avg_session_seconds,
        MIN(log_date) as first_usage,
        MAX(log_date) as last_usage
            FROM app_usage
            WHERE user = ? AND application_name = ?
            GROUP BY user, application_name
            """
        params = (user, application_name)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_app_hours",
            "description": "Hours spent by user on specific application",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "user": record.get("user"),
                "application_name": record.get("application_name"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "session_count": record.get("session_count"),
                "avg_session_minutes": round(record.get("avg_session_seconds", 0) / 60, 2),
                "first_usage": record.get("first_usage"),
                "last_usage": record.get("last_usage"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_app_hours_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_app_hours",
                "error": str(e),
                "message": "Failed to execute user_app_hours"
            }, indent=2)
        )]


user_app_hours_tool = Tool(
    name="user_app_hours",
    description="Hours spent by user on specific application",
    inputSchema={
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "User identifier to analyze"
        },
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
            }
        },
        "required": ["user", "application_name"],
        "additionalProperties": False
    }
)

user_app_hours_tool.handler = user_app_hours_handler
