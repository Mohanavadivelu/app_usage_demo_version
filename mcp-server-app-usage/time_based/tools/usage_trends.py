"""
Tool: Usage Trends
Category: Time Based
Feature ID: 25

Description:
    Weekly/monthly usage trends

Parameters:
    - period_type (str, optional): Period Type parameter, - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - application_name (str, required): Application name

Returns:
    - Weekly/monthly usage trends with detailed analytics

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


async def usage_trends_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the usage_trends tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'period_type', 'start_date', 'end_date', 'application_name'}
        )
        
        period_type = validated_params.get('period_type')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        application_name = validated_params.get('application_name')
        
        # Execute main query
        base_query = """
            SELECT 
        strftime('%Y-%W', log_date) as period,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT user) as unique_users,
        COUNT(DISTINCT application_name) as unique_apps,
        COUNT(*) as total_sessions
            FROM app_usage
            GROUP BY strftime('%Y-%W', log_date)
            ORDER BY period
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
            "tool": "usage_trends",
            "description": "Weekly/monthly usage trends",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "period": record.get("period"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_users": record.get("unique_users"),
                "unique_apps": record.get("unique_apps"),
                "total_sessions": record.get("total_sessions"),
                "growth_rate": record.get("growth_rate"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in usage_trends_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "usage_trends",
                "error": str(e),
                "message": "Failed to execute usage_trends"
            }, indent=2)
        )]


usage_trends_tool = Tool(
    name="usage_trends",
    description="Weekly/monthly usage trends",
    inputSchema={
        "type": "object",
        "properties": {
            "period_type": {
                "type": "string",
                "description": "Period Type parameter"
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
        "application_name": {
                "type": "string",
                "description": "Application name to analyze"
        }
,
        
        "additionalProperties": False
    }
)

usage_trends_tool.handler = usage_trends_handler
