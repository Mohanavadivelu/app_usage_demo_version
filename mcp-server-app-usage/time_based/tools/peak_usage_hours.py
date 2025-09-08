"""
Tool: Peak Usage Hours
Category: Time Based
Feature ID: 26

Description:
    Identify peak usage hours

Parameters:
    - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - application_name (str, required): Application name

Returns:
    - Identify peak usage hours with detailed analytics

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


async def peak_usage_hours_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the peak_usage_hours tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'start_date', 'end_date', 'application_name'}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        application_name = validated_params.get('application_name')
        
        # Execute main query
        base_query = """
            SELECT 
        strftime('%H', created_at) as hour,
        COUNT(*) as session_count,
        COUNT(DISTINCT user) as unique_users,
        SUM(duration_seconds) as total_seconds,
        AVG(duration_seconds) as avg_session_seconds
            FROM app_usage
            WHERE created_at IS NOT NULL
            GROUP BY strftime('%H', created_at)
            ORDER BY session_count DESC
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
            "tool": "peak_usage_hours",
            "description": "Identify peak usage hours",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "hour": record.get("hour"),
                "session_count": record.get("session_count"),
                "unique_users": record.get("unique_users"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "avg_session_minutes": round(record.get("avg_session_seconds", 0) / 60, 2),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in peak_usage_hours_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "peak_usage_hours",
                "error": str(e),
                "message": "Failed to execute peak_usage_hours"
            }, indent=2)
        )]


peak_usage_hours_tool = Tool(
    name="peak_usage_hours",
    description="Identify peak usage hours",
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
        "application_name": {
                "type": "string",
                "description": "Application name to analyze"
        }
,
        
        "additionalProperties": False
    }
)

peak_usage_hours_tool.handler = peak_usage_hours_handler
