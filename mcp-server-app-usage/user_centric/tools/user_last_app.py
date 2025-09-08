"""
Tool: User Last App
Category: User Centric
Feature ID: 18

Description:
    Find the last application used by a user

Parameters:
    - user (str, required): User identifier

Returns:
    - Find the last application used by a user with detailed analytics

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


async def user_last_app_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_last_app tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['user'],
            optional=[]
        )
        
        user = validated_params.get('user')
        
        # Execute main query
        query = """
            SELECT 
        user,
        application_name,
        log_date,
        duration_seconds,
        platform
            FROM app_usage
            WHERE user = ?
            ORDER BY log_date DESC, id DESC
            LIMIT 1
            """
        params = (user,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_last_app",
            "description": "Find the last application used by a user",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "user": record.get("user"),
                "last_application": record.get("last_application"),
                "last_usage_date": record.get("last_usage_date"),
                "session_duration_minutes": round(record.get("avg_session_seconds", 0) / 60, 2),
                "platform": record.get("platform"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_last_app_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_last_app",
                "error": str(e),
                "message": "Failed to execute user_last_app"
            }, indent=2)
        )]


user_last_app_tool = Tool(
    name="user_last_app",
    description="Find the last application used by a user",
    inputSchema={
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "User identifier to analyze"
        }
        },
        "required": ["user"],
        "additionalProperties": False
    }
)

user_last_app_tool.handler = user_last_app_handler
