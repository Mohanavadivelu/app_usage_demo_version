"""
Tool: Top Apps By Usage
Category: Usage Stats
Feature ID: 11

Description:
    Rank applications by total usage time

Parameters:
    - top_n (int, optional): Number of top results
    - start_date (str, optional): Start date for analysis
    - end_date (str, optional): End date for analysis
    - platform (str, optional): Platform to filter by

Returns:
    - Rank applications by total usage time with detailed analytics

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


async def top_apps_by_usage_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the top_apps_by_usage tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'top_n', 'start_date', 'end_date', 'platform'}
        )
        
        top_n = validated_params.get('top_n', 10)
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        platform = validated_params.get('platform')
        
        # Execute main query
        base_query = """
            SELECT 
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT user) as unique_users,
        COUNT(*) as total_sessions,
        AVG(duration_seconds) as avg_session_seconds
            FROM app_usage
            GROUP BY application_name
            ORDER BY total_seconds DESC
        """
        
        filters = {}
        if platform:
            filters['platform'] = platform
        if start_date:
            filters['log_date'] = (start_date, end_date) if end_date else (start_date, '9999-12-31')
        elif end_date:
            filters['log_date'] = ('1900-01-01', end_date)
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            limit=top_n
        )
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "top_apps_by_usage",
            "description": "Rank applications by total usage time",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "rank": i + 1,
                "application_name": record.get("application_name"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_users": record.get("unique_users"),
                "total_sessions": record.get("total_sessions"),
                "avg_session_minutes": round(record.get("avg_session_seconds", 0) / 60, 2)
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in top_apps_by_usage_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "top_apps_by_usage",
                "error": str(e),
                "message": "Failed to execute top_apps_by_usage"
            }, indent=2)
        )]


top_apps_by_usage_tool = Tool(
    name="top_apps_by_usage",
    description="Rank applications by total usage time",
    inputSchema={
        "type": "object",
        "properties": {
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
            },
            "platform": {
                "type": "string",
                "description": "Platform to filter by"
            }
        },
        "additionalProperties": False
    }
)

top_apps_by_usage_tool.handler = top_apps_by_usage_handler
