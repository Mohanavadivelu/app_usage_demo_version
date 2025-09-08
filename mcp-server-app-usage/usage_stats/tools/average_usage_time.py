"""
Tool: Average Usage Time
Category: Usage Stats
Feature ID: 10

Description:
    Calculate average time spent per user per application

Parameters:
    - application_name (str, optional): Application name to filter by
    - start_date (str, optional): Start date for analysis
    - end_date (str, optional): End date for analysis
    - limit (int, optional): Maximum number of results

Returns:
    - Calculate average time spent per user per application with detailed analytics

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


async def average_usage_time_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the average_usage_time tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'application_name', 'start_date', 'end_date', 'limit'}
        )
        
        application_name = validated_params.get('application_name')
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Execute main query
        base_query = """
            SELECT 
        application_name,
        user,
        AVG(duration_seconds) as avg_seconds,
        COUNT(*) as session_count,
        SUM(duration_seconds) as total_seconds,
        MIN(log_date) as first_usage,
        MAX(log_date) as last_usage
            FROM app_usage
            GROUP BY application_name, user
            ORDER BY avg_seconds DESC
        """
        
        filters = {}
        if application_name:
            filters['application_name'] = application_name
        if start_date:
            filters['log_date'] = (start_date, end_date) if end_date else (start_date, '9999-12-31')
        elif end_date:
            filters['log_date'] = ('1900-01-01', end_date)
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            limit=limit
        )
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "average_usage_time",
            "description": "Calculate average time spent per user per application",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "application_name": record.get("application_name"),
                "user": record.get("user"),
                "average_minutes": round(record.get("avg_seconds", 0) / 60, 2),
                "session_count": record.get("session_count"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "first_usage": record.get("first_usage"),
                "last_usage": record.get("last_usage")
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in average_usage_time_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "average_usage_time",
                "error": str(e),
                "message": "Failed to execute average_usage_time"
            }, indent=2)
        )]


average_usage_time_tool = Tool(
    name="average_usage_time",
    description="Calculate average time spent per user per application",
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
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            }
        },
        "additionalProperties": False
    }
)

average_usage_time_tool.handler = average_usage_time_handler
