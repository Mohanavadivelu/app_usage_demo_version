"""
Tool: User App Matrix
Category: Cross Analysis
Feature ID: 29

Description:
    Cross-tab display of users vs applications matrix showing usage patterns

Parameters:
    - start_date (str, optional): Start date for analysis
    - end_date (str, optional): End date for analysis
    - limit (int, optional): Maximum number of results

Returns:
    - Cross-tab matrix of users vs applications with detailed analytics

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


async def user_app_matrix_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_app_matrix tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={"start_date", "end_date", "limit"}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        
        # Execute main query
        base_query = """
            SELECT 
        user,
        application_name,
        SUM(duration_seconds) as total_seconds,
        COUNT(*) as session_count,
        MAX(log_date) as last_usage,
        AVG(duration_seconds) as avg_session_seconds
            FROM app_usage
            GROUP BY user, application_name
            ORDER BY user, total_seconds DESC
        """
        
        filters = {}
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
        
        # Process results into matrix format
        user_app_matrix = {}
        total_usage_by_user = {}
        
        for record in result.data:
            user = record['user']
            app = record['application_name']
            hours = round(record['total_seconds'] / 3600, 2)
            
            if user not in user_app_matrix:
                user_app_matrix[user] = {}
                total_usage_by_user[user] = 0
            
            user_app_matrix[user][app] = {
                'total_hours': hours,
                'session_count': record['session_count'],
                'last_usage': record['last_usage'],
                'avg_session_minutes': round(record['avg_session_seconds'] / 60, 2)
            }
            total_usage_by_user[user] += hours
        
        # Calculate usage percentages
        matrix_results = []
        for user, apps in user_app_matrix.items():
            user_total = total_usage_by_user[user]
            for app, data in apps.items():
                usage_percentage = round((data['total_hours'] / user_total) * 100, 2) if user_total > 0 else 0
                matrix_results.append({
                    'user': user,
                    'application_name': app,
                    'total_hours': data['total_hours'],
                    'session_count': data['session_count'],
                    'last_usage': data['last_usage'],
                    'avg_session_minutes': data['avg_session_minutes'],
                    'usage_percentage': usage_percentage
                })
        
        response_data = {
            "tool": "user_app_matrix",
            "description": "Cross-tab display of users vs applications matrix",
            "total_records": len(matrix_results),
            "query_time_ms": result.query_time_ms,
            "matrix_summary": {
                "total_users": len(user_app_matrix),
                "total_user_app_combinations": len(matrix_results),
                "avg_apps_per_user": round(len(matrix_results) / len(user_app_matrix), 2) if user_app_matrix else 0
            },
            "results": matrix_results
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_app_matrix_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_app_matrix",
                "error": str(e),
                "message": "Failed to execute user_app_matrix"
            }, indent=2)
        )]


user_app_matrix_tool = Tool(
    name="user_app_matrix",
    description="Cross-tab display of users vs applications matrix showing usage patterns",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date for analysis (YYYY-MM-DD format)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "end_date": {
                "type": "string", 
                "description": "End date for analysis (YYYY-MM-DD format)",
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

user_app_matrix_tool.handler = user_app_matrix_handler
