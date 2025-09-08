"""
Tool: User Applications
Category: User Centric
Feature ID: 15

Description:
    List all applications used by a user

Parameters:
    - user (str, required): User identifier, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - limit (int, optional): Maximum number of results

Returns:
    - List all applications used by a user with detailed analytics

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


async def user_applications_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_applications tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['user'],
            optional=['start_date', 'end_date', 'limit']
        )
        
        user = validated_params.get('user')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Execute main query
        query = """
            SELECT 
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as session_count,
        AVG(duration_seconds) as avg_session_seconds,
        MIN(log_date) as first_usage,
        MAX(log_date) as last_usage,
        COUNT(DISTINCT platform) as platforms_used
            FROM app_usage
            WHERE user = ?
            GROUP BY application_name
            ORDER BY total_seconds DESC
            """
        params = (user,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_applications",
            "description": "List all applications used by a user",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "application_name": record.get("application_name"),
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
        logger.error(f"Error in user_applications_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_applications",
                "error": str(e),
                "message": "Failed to execute user_applications"
            }, indent=2)
        )]


user_applications_tool = Tool(
    name="user_applications",
    description="List all applications used by a user",
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
        },
        "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
        }
,
        "required": ['user'],
        "additionalProperties": False
    }
)

user_applications_tool.handler = user_applications_handler
