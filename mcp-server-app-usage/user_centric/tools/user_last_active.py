"""
Tool: User Last Active
Category: User Centric
Feature ID: 19

Description:
    When was a user last active

Parameters:
    - user (str, required): User identifier

Returns:
    - When was a user last active with detailed analytics

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


async def user_last_active_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_last_active tool request."""
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
        MAX(log_date) as last_active_date,
        COUNT(DISTINCT log_date) as active_days,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as total_sessions
            FROM app_usage
            WHERE user = ?
            GROUP BY user
            """
        params = (user,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_last_active",
            "description": "When was a user last active",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "user": record.get("user"),
                "last_active_date": record.get("last_active_date"),
                "active_days": record.get("active_days"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "total_sessions": record.get("total_sessions"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_last_active_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_last_active",
                "error": str(e),
                "message": "Failed to execute user_last_active"
            }, indent=2)
        )]


user_last_active_tool = Tool(
    name="user_last_active",
    description="When was a user last active",
    inputSchema={
        "type": "object",
        "properties": {
            "user": {
                "type": "string",
                "description": "User identifier to analyze"
        }
,
        "required": ['user'],
        "additionalProperties": False
    }
)

user_last_active_tool.handler = user_last_active_handler
