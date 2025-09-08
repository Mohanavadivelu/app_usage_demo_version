"""
Tool: User Count Stats
Category: Usage Statistics
Feature ID: 9

Description:
    Display the number of users using each application with detailed statistics.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD)
    - limit (int, optional): Maximum number of applications to return
    - min_users (int, optional): Minimum number of users to include app

Returns:
    - List of applications with user count statistics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters, build_query

logger = logging.getLogger(__name__)


async def user_count_stats_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the user_count_stats tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'start_date', 'end_date', 'limit', 'min_users'}
        )
        
        start_date = validated_params.get('start_date')
        end_date = validated_params.get('end_date')
        limit = validated_params.get('limit', 100)
        min_users = validated_params.get('min_users', 1)
        
        # Build query with optional date filters
        base_query = """
        SELECT 
            application_name,
            COUNT(DISTINCT user) as unique_users,
            COUNT(*) as total_sessions,
            SUM(duration_seconds) as total_seconds,
            AVG(duration_seconds) as avg_session_seconds,
            MIN(log_date) as first_usage_date,
            MAX(log_date) as last_usage_date,
            COUNT(DISTINCT platform) as platforms_used
        FROM app_usage
        """
        
        filters = {}
        if start_date:
            filters['log_date'] = (start_date, end_date) if end_date else (start_date, '9999-12-31')
        elif end_date:
            filters['log_date'] = ('1900-01-01', end_date)
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="application_name",
            order_by="unique_users DESC",
            limit=limit
        )
        
        # Add HAVING clause for minimum users
        if min_users > 1:
            query = query.replace("ORDER BY", f"HAVING COUNT(DISTINCT user) >= {min_users} ORDER BY")
        
        result = execute_analytics_query(query, params)
        
        response_data = {
            "tool": "user_count_stats",
            "description": "User count statistics per application",
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "filters": {
                "min_users": min_users,
                "limit": limit
            },
            "total_applications": result.total_count,
            "applications": []
        }
        
        total_unique_users = set()
        total_sessions = 0
        
        for app in result.data:
            total_sessions += app["total_sessions"]
            
            app_info = {
                "application_name": app["application_name"],
                "unique_users": app["unique_users"],
                "total_sessions": app["total_sessions"],
                "total_usage_hours": round(app["total_seconds"] / 3600, 2),
                "average_session_minutes": round(app["avg_session_seconds"] / 60, 2),
                "sessions_per_user": round(app["total_sessions"] / app["unique_users"], 2),
                "first_usage_date": app["first_usage_date"],
                "last_usage_date": app["last_usage_date"],
                "platforms_used": app["platforms_used"],
                "user_engagement": "High" if app["unique_users"] > 10 else "Medium" if app["unique_users"] > 5 else "Low"
            }
            response_data["applications"].append(app_info)
        
        # Get total unique users across all apps for summary
        total_users_query = """
        SELECT COUNT(DISTINCT user) as total_unique_users
        FROM app_usage
        """
        if filters:
            total_users_query, total_params = build_query(
        base_query=total_users_query,
        filters=filters
            )
        else:
            total_params = ()
        
        total_users_result = execute_analytics_query(total_users_query, total_params)
        total_unique_users_count = total_users_result.data[0]["total_unique_users"] if total_users_result.data else 0
        
        response_data["summary"] = {
            "total_applications_analyzed": len(result.data),
            "total_unique_users_across_all_apps": total_unique_users_count,
            "total_sessions_analyzed": total_sessions,
            "average_users_per_app": round(sum(app["unique_users"] for app in result.data) / len(result.data), 2) if result.data else 0,
            "most_popular_app": result.data[0]["application_name"] if result.data else None,
            "least_popular_app": result.data[-1]["application_name"] if result.data else None
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in user_count_stats_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "user_count_stats",
                "error": str(e),
                "message": "Failed to retrieve user count statistics"
            }, indent=2)
        )]


user_count_stats_tool = Tool(
    name="user_count_stats",
    description="Display the number of users using each application with detailed statistics",
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
                "description": "Maximum number of applications to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            },
            "min_users": {
                "type": "integer",
                "description": "Minimum number of users required to include application (default: 1)",
                "minimum": 1,
                "default": 1
            }
        },
        "additionalProperties": False
    }
)

user_count_stats_tool.handler = user_count_stats_handler
