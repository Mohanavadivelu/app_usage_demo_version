"""
Tool: Total Usage Period
Category: Usage Stats
Feature ID: 13

Description:
    Calculate total usage time for time periods

Parameters:
    - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - period_type (str, optional): Period Type parameter

Returns:
    - Calculate total usage time for time periods with detailed analytics

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


async def total_usage_period_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the total_usage_period tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'start_date', 'end_date', 'period_type'}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        period_type = validated_params.get('period_type')
        
        # Execute main query
        base_query = """
            SELECT 
        log_date,
        SUM(duration_seconds) as total_seconds,
        COUNT(DISTINCT user) as unique_users,
        COUNT(DISTINCT application_name) as unique_apps,
        COUNT(*) as total_sessions
            FROM app_usage
            GROUP BY log_date
            ORDER BY log_date
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
            "tool": "total_usage_period",
            "description": "Calculate total usage time for time periods",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "date": record.get("date"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "unique_users": record.get("unique_users"),
                "unique_apps": record.get("unique_apps"),
                "total_sessions": record.get("total_sessions"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in total_usage_period_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "total_usage_period",
                "error": str(e),
                "message": "Failed to execute total_usage_period"
            }, indent=2)
        )]


total_usage_period_tool = Tool(
    name="total_usage_period",
    description="Calculate total usage time for time periods",
    inputSchema={
        "type": "object",
        "properties": {
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
            "period_type": {
                "type": "string",
                "description": "Period Type parameter"
            }
        },
        "additionalProperties": False
    }
)

total_usage_period_tool.handler = total_usage_period_handler
