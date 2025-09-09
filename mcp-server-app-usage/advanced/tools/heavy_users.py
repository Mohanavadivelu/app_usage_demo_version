"""
Tool: Heavy Users
Category: Advanced
Feature ID: 39

Description:
    Identify heavy users based on usage patterns. This tool finds users
    with exceptionally high usage across applications, helping identify
    power users and usage outliers.

Parameters:
    - limit (int, optional): Maximum number of users to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - threshold_hours (float, optional): Minimum hours to be considered heavy user (default: 50.0)
    - sort_by (str, optional): Sort field (total_hours, sessions, apps_used)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with heavy user analysis and insights

Examples:
    Basic usage:
    Input: {}
    Output: Top 100 heavy users across all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "threshold_hours": 100.0}
    Output: Heavy Chrome users with 100+ hours usage

Database Tables Used:
    - app_usage: For user activity and usage duration

Related Tools:
    - session_length_analysis: Analyze session patterns
    - inactive_users: Compare with low-usage users

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def heavy_users(
    limit: int = 100,
    app_name: Optional[str] = None,
    threshold_hours: float = 50.0,
    sort_by: str = "total_hours",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Identify heavy users based on usage patterns.
    
    Args:
        limit: Maximum number of users to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        threshold_hours: Minimum hours to be considered heavy user (default: 50.0, max: 1000.0)
        sort_by: Field to sort by (total_hours, sessions, apps_used, avg_session_hours)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing heavy user analysis and insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "across all applications"
            ctx.info(f"Identifying heavy users {filter_desc}, threshold: {threshold_hours}h, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        if threshold_hours < 1.0 or threshold_hours > 1000.0:
            raise ValueError("threshold_hours must be between 1.0 and 1000.0")
        
        valid_sort_fields = ['total_hours', 'sessions', 'apps_used', 'avg_session_hours']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        if ctx:
            ctx.report_progress(25, 100, "Analyzing heavy user patterns...")
        
        # Build query to identify heavy users
        if app_name:
            # Single app analysis
            base_query = """
            SELECT 
                user,
                application_name,
                COUNT(*) as sessions,
                SUM(duration_seconds) as total_seconds,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(log_date) as first_session_date,
                MAX(log_date) as last_session_date,
                1 as apps_used
            FROM app_usage
            WHERE duration_seconds > 0
            """
        else:
            # Multi-app analysis
            base_query = """
            SELECT 
                user,
                'Multiple Apps' as application_name,
                COUNT(*) as sessions,
                SUM(duration_seconds) as total_seconds,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(log_date) as first_session_date,
                MAX(log_date) as last_session_date,
                COUNT(DISTINCT application_name) as apps_used
            FROM app_usage
            WHERE duration_seconds > 0
            """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        
        # Add having clause for threshold
        threshold_seconds = threshold_hours * 3600
        having_clause = f"SUM(duration_seconds) >= {threshold_seconds}"
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'total_hours': 'total_seconds',
            'sessions': 'sessions',
            'apps_used': 'apps_used',
            'avg_session_hours': 'avg_session_seconds'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="user" if not app_name else "user, application_name",
            having=having_clause,
            order_by=order_clause,
            limit=limit
        )
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} heavy users in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing heavy user analysis...")
        
        # Format response
        response_data = {
            "tool": "heavy_users",
            "description": "Heavy user identification and analysis",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "threshold_hours": threshold_hours,
                "app_name_filter": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "heavy_users": []
        }
        
        # Process heavy user data
        total_heavy_users = len(result.data)
        total_usage_hours = 0
        total_sessions = 0
        usage_categories = {"extreme": 0, "very_high": 0, "high": 0, "moderate": 0}
        
        for record in result.data:
            total_seconds = record["total_seconds"] or 0
            total_hours = total_seconds / 3600
            avg_session_seconds = record["avg_session_seconds"] or 0
            avg_session_hours = avg_session_seconds / 3600
            
            total_usage_hours += total_hours
            total_sessions += record["sessions"]
            
            # Categorize usage intensity
            if total_hours >= 500:
                usage_category = "extreme"
                usage_categories["extreme"] += 1
            elif total_hours >= 200:
                usage_category = "very_high"
                usage_categories["very_high"] += 1
            elif total_hours >= 100:
                usage_category = "high"
                usage_categories["high"] += 1
            else:
                usage_category = "moderate"
                usage_categories["moderate"] += 1
            
            # Generate user insights
            insights = []
            recommendations = []
            
            if total_hours >= 500:
                insights.append("Extreme power user - potential product champion")
                recommendations.append("Engage for feedback and beta testing")
            elif total_hours >= 200:
                insights.append("Very high usage - core user segment")
                recommendations.append("Target for premium features and loyalty programs")
            elif total_hours >= 100:
                insights.append("High usage - engaged user")
                recommendations.append("Monitor for satisfaction and retention")
            
            if avg_session_hours > 4:
                insights.append("Very long session durations")
            elif avg_session_hours > 2:
                insights.append("Long session durations")
            
            if record["apps_used"] > 5:
                insights.append("Multi-app power user")
                recommendations.append("Consider cross-app integration features")
            
            # Calculate usage consistency
            days_active = (record["last_session_date"] and record["first_session_date"]) and \
                         (record["last_session_date"] != record["first_session_date"])
            
            user_info = {
                "user": record["user"],
                "application_context": record["application_name"],
                "usage_metrics": {
                    "total_hours": round(total_hours, 2),
                    "total_sessions": record["sessions"],
                    "apps_used": record["apps_used"],
                    "average_session_hours": round(avg_session_hours, 2),
                    "usage_category": usage_category
                },
                "timeline": {
                    "first_session_date": record["first_session_date"],
                    "last_session_date": record["last_session_date"],
                    "active_period_days": days_active
                },
                "insights": insights,
                "recommendations": recommendations
            }
            response_data["heavy_users"].append(user_info)
        
        # Calculate statistics
        avg_usage_hours = total_usage_hours / total_heavy_users if total_heavy_users > 0 else 0
        avg_sessions = total_sessions / total_heavy_users if total_heavy_users > 0 else 0
        
        # Add summary statistics
        response_data["summary"] = {
            "total_heavy_users": total_heavy_users,
            "total_usage_hours": round(total_usage_hours, 2),
            "total_sessions": total_sessions,
            "average_usage_per_user": round(avg_usage_hours, 2),
            "average_sessions_per_user": round(avg_sessions, 2),
            "usage_intensity_distribution": usage_categories
        }
        
        # Add insights and patterns
        response_data["patterns"] = {
            "top_power_users": [
                {
                    "user": user["user"],
                    "hours": user["usage_metrics"]["total_hours"],
                    "category": user["usage_metrics"]["usage_category"]
                }
                for user in sorted(response_data["heavy_users"], 
                                 key=lambda x: x["usage_metrics"]["total_hours"], reverse=True)
            ][:10],
            "most_engaged_users": [
                {
                    "user": user["user"],
                    "sessions": user["usage_metrics"]["total_sessions"],
                    "avg_session_hours": user["usage_metrics"]["average_session_hours"]
                }
                for user in sorted(response_data["heavy_users"], 
                                 key=lambda x: x["usage_metrics"]["total_sessions"], reverse=True)
            ][:10],
            "usage_insights": {
                "extreme_users_percentage": round((usage_categories["extreme"] / total_heavy_users * 100), 2) if total_heavy_users > 0 else 0,
                "power_user_concentration": usage_categories["extreme"] + usage_categories["very_high"],
                "average_apps_per_heavy_user": round(sum(user["usage_metrics"]["apps_used"] for user in response_data["heavy_users"]) / total_heavy_users, 2) if total_heavy_users > 0 else 0
            }
        }
        
        # Add business recommendations
        response_data["business_recommendations"] = {
            "engagement_strategies": [
                "Create VIP program for extreme users",
                "Implement referral rewards for power users",
                "Develop advanced features for heavy usage patterns"
            ],
            "retention_focus": [
                "Monitor satisfaction of top users",
                "Provide premium support channels",
                "Gather feedback for product roadmap"
            ],
            "monetization_opportunities": [
                "Target premium subscriptions to heavy users",
                "Offer usage-based pricing tiers",
                "Create enterprise solutions for extreme users"
            ]
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Heavy user analysis complete")
            ctx.info(f"Analysis complete: {total_heavy_users} heavy users, {avg_usage_hours:.1f}h avg usage")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in heavy_users: {e}")
        if ctx:
            ctx.error(f"Failed to identify heavy users: {e}")
        
        return {
            "tool": "heavy_users",
            "error": str(e),
            "message": "Failed to identify heavy users"
        }
