"""
Tool: Platform Usage Stats
Category: Usage Stats
Feature ID: 14

Description:
    Applications used most on each platform

Parameters:
    - platform (str, optional): Platform parameter, - limit (int, optional): Maximum number of results, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis

Returns:
    - Applications used most on each platform with detailed analytics

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


async def platform_usage_stats_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the platform_usage_stats tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'platform', 'limit', 'start_date', 'end_date'}
        )
        
        platform = validated_params.get('platform')
        limit = validated_params.get('limit', 100)
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        
        # Execute main query
        base_query = """
            SELECT 
        platform,
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT user) as unique_users,
        COUNT(*) as total_sessions
            FROM app_usage
            GROUP BY platform, application_name
            ORDER BY platform, total_seconds DESC
            """
        
        filters = {}
        if start_date:
            filters['log_date'] = (start_date, end_date) if end_date else (start_date, '9999-12-31')
        elif end_date:
            filters['log_date'] = ('1900-01-01', end_date)
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            limit=limit if 'limit' in locals() else None
        )
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "platform_usage_stats",
            "description": "Applications used most on each platform",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "platform": record.get("platform"),
                "application_name": record.get("application_name"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_users": record.get("unique_users"),
                "total_sessions": record.get("total_sessions"),
                "rank_in_platform": record.get("rank_in_platform"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in platform_usage_stats_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "platform_usage_stats",
                "error": str(e),
                "message": "Failed to execute platform_usage_stats"
            }, indent=2)
        )]


platform_usage_stats_tool = Tool(
    name="platform_usage_stats",
    description="Applications used most on each platform",
    inputSchema={
        "type": "object",
        "properties": {
            "platform": {
                "type": "string",
                "description": "Platform parameter"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
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
        "additionalProperties": False
    }
)

platform_usage_stats_tool.handler = platform_usage_stats_handler
