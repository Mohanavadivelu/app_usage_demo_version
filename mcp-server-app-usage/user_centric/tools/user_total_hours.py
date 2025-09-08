"""
Tool: User Total Hours
Category: User Centric
Feature ID: 16

Description:
    Calculate total hours for a user across all apps

Parameters:
    - user (str, required): User identifier, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis

Returns:
    - Calculate total hours for a user across all apps with detailed analytics

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


async def user_total_hours_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_total_hours tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['user'],
            optional=['start_date', 'end_date']
        )
        
        user = validated_params.get('user')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        
        # Execute main query
        query = """
            SELECT 
        user,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT application_name) as unique_apps,
        COUNT(*) as total_sessions,
        AVG(duration_seconds) as avg_session_seconds,
        MIN(log_date) as first_usage,
        MAX(log_date) as last_usage
            FROM app_usage
            WHERE user = ?
            GROUP BY user
            """
        params = (user,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_total_hours",
            "description": "Calculate total hours for a user across all apps",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "user": record.get("user"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_apps": record.get("unique_apps"),
                "total_sessions": record.get("total_sessions"),
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
        logger.error(f"Error in user_total_hours_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_total_hours",
                "error": str(e),
                "message": "Failed to execute user_total_hours"
            }, indent=2)
        )]


user_total_hours_tool = Tool(
    name="user_total_hours",
    description="Calculate total hours for a user across all apps",
    inputSchema={
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "User identifier to analyze"
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
        "required": ["user"],
        "additionalProperties": False
    }
)

user_total_hours_tool.handler = user_total_hours_handler
