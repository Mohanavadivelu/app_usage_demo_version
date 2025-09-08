"""
Tool: Onboarding Trend
Category: Time Based
Feature ID: 27

Description:
    Track new application adoptions

Parameters:
    - start_date (str, optional): Start date for analysis, - end_date (str, optional): End date for analysis, - limit (int, optional): Maximum number of results

Returns:
    - Track new application adoptions with detailed analytics

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


async def onboarding_trend_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the onboarding_trend tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'start_date', 'end_date', 'limit'}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Execute main query
        base_query = """
            SELECT 
        application_name,
        MIN(log_date) as first_adoption_date,
        COUNT(DISTINCT user) as total_adopters,
        COUNT(*) as total_sessions,
        SUM(duration_seconds) as total_seconds
            FROM app_usage
            GROUP BY application_name
            ORDER BY first_adoption_date DESC
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
            "tool": "onboarding_trend",
            "description": "Track new application adoptions",
            "total_records": result.total_count,
            "query_time_ms": result.query_time_ms,
            "results": []
        }
        
        for i, record in enumerate(result.data):
            processed_record = {
                "application_name": record.get("application_name"),
                "first_adoption_date": record.get("first_adoption_date"),
                "total_adopters": record.get("total_adopters"),
                "total_sessions": record.get("total_sessions"),
                "total_hours": round(record.get("total_seconds", 0) / 3600, 2),
            }
            response_data['results'].append(processed_record)
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in onboarding_trend_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "onboarding_trend",
                "error": str(e),
                "message": "Failed to execute onboarding_trend"
            }, indent=2)
        )]


onboarding_trend_tool = Tool(
    name="onboarding_trend",
    description="Track new application adoptions",
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

onboarding_trend_tool.handler = onboarding_trend_handler
