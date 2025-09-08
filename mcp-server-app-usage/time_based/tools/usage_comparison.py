"""
Tool: Usage Comparison
Category: Time Based
Feature ID: 28

Description:
    Compare usage between date ranges

Parameters:
    - period1_start (str, optional): Period1 Start parameter, - period1_end (str, optional): Period1 End parameter, - period2_start (str, optional): Period2 Start parameter, - period2_end (str, optional): Period2 End parameter

Returns:
    - Compare usage between date ranges with detailed analytics

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


async def usage_comparison_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the usage_comparison tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'period1_start', 'period1_end', 'period2_start', 'period2_end'}
        )
        
        period1_start = validated_params.get('period1_start')
        period1_end = validated_params.get('period1_end')
        period2_start = validated_params.get('period2_start')
        period2_end = validated_params.get('period2_end')
        
        # Execute main query
        query = """
            SELECT 
        application_name,
        SUM(CASE WHEN log_date BETWEEN ? AND ? THEN duration_seconds ELSE 0 END) as period1_seconds,
        SUM(CASE WHEN log_date BETWEEN ? AND ? THEN duration_seconds ELSE 0 END) as period2_seconds,
        COUNT(DISTINCT CASE WHEN log_date BETWEEN ? AND ? THEN user END) as period1_users,
        COUNT(DISTINCT CASE WHEN log_date BETWEEN ? AND ? THEN user END) as period2_users
            FROM app_usage
            GROUP BY application_name
            HAVING period1_seconds > 0 OR period2_seconds > 0
            ORDER BY (period2_seconds - period1_seconds) DESC
            """
        params = ()
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "usage_comparison",
            "description": "Compare usage between date ranges",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "application_name": record.get("application_name"),
                "period1_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "period2_hours": round(record.get("total_seconds", 0) / 3600, 2),
                "period1_users": record.get("period1_users"),
                "period2_users": record.get("period2_users"),
                "usage_change_percent": record.get("usage_change_percent"),
                "user_change_percent": record.get("user_change_percent"),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in usage_comparison_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "usage_comparison",
                "error": str(e),
                "message": "Failed to execute usage_comparison"
            }, indent=2)
        )]


usage_comparison_tool = Tool(
    name="usage_comparison",
    description="Compare usage between date ranges",
    inputSchema={
        "type": "object",
        "properties": {
            "period1_start": {
                "type": "string",
                "description": "Period1 Start parameter"
        },
        "period1_end": {
                "type": "string",
                "description": "Period1 End parameter"
        },
        "period2_start": {
                "type": "string",
                "description": "Period2 Start parameter"
        },
        "period2_end": {
                "type": "string",
                "description": "Period2 End parameter"
            }
        },
        "additionalProperties": False
    }
)

usage_comparison_tool.handler = usage_comparison_handler
