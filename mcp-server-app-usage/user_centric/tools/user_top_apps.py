"""
Tool: User Top Apps
Category: User Centric
Feature ID: 20

Description:
    Top N applications for a specific user

Parameters:
    - user (str, required): User identifier, - top_n (int, optional): Number of top results, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis

Returns:
    - Top N applications for a specific user with detailed analytics

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


async def user_top_apps_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_top_apps tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['user'],
            optional=['top_n', 'start_date', 'end_date']
        )
        
        user = validated_params.get('user')
        top_n = validated_params.get('top_n', 10)
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        
        # Execute main query
        query = """
            SELECT 
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as session_count,
        AVG(duration_seconds) as avg_session_seconds,
        MAX(log_date) as last_usage
            FROM app_usage
            WHERE user = ?
            GROUP BY application_name
            ORDER BY total_seconds DESC
            """
        params = (user,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_top_apps",
            "description": "Top N applications for a specific user",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "rank": i + 1,
                "application_name": record.get("application_name"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "session_count": record.get("session_count"),
                "avg_session_minutes": round(record.get("avg_session_seconds", 0) / 60, 2),
                "last_usage": record.get("last_usage"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_top_apps_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_top_apps",
                "error": str(e),
                "message": "Failed to execute user_top_apps"
            }, indent=2)
        )]


user_top_apps_tool = Tool(
    name="user_top_apps",
    description="Top N applications for a specific user",
    inputSchema={
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "User identifier to analyze"
        },
        "top_n": {
                "type": "integer",
                "description": "Top N items (default: 10)",
                "minimum": 1,
                "maximum": 100,
                "default": 10
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
,
        "required": ['user'],
        "additionalProperties": False
    }
)

user_top_apps_tool.handler = user_top_apps_handler
