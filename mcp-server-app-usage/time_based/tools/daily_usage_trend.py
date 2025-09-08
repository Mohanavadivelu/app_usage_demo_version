"""
Tool: Daily Usage Trend
Category: Time Based
Feature ID: 24

Description:
    Daily usage trends for applications

Parameters:
    - application_name (str, required): Application name, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis

Returns:
    - Daily usage trends for applications with detailed analytics

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


async def daily_usage_trend_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the daily_usage_trend tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=['application_name'],
            optional=['start_date', 'end_date']
        )
        
        application_name = validated_params.get('application_name')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        
        # Execute main query
        query = """
            SELECT 
        log_date,
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT user) as unique_users,
        COUNT(*) as total_sessions
            FROM app_usage
            WHERE application_name = ?
            GROUP BY log_date, application_name
            ORDER BY log_date
            """
        params = (application_name,)
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "daily_usage_trend",
            "description": "Daily usage trends for applications",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "date": record.get("date"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_users": record.get("unique_users"),
                "total_sessions": record.get("total_sessions"),
                "trend_direction": record.get("trend_direction"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in daily_usage_trend_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "daily_usage_trend",
                "error": str(e),
                "message": "Failed to execute daily_usage_trend"
            }, indent=2)
        )]


daily_usage_trend_tool = Tool(
    name="daily_usage_trend",
    description="Daily usage trends for applications",
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
        }
        },
        "required": ["application_name"],
        "additionalProperties": False
    }
)

daily_usage_trend_tool.handler = daily_usage_trend_handler
