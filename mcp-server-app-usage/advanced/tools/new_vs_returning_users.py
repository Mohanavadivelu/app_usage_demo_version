"""
Tool: New vs Returning Users
Category: Advanced
Feature ID: 42

Description:
    Analyze new vs returning user patterns. This tool provides insights
    into user acquisition, retention, and behavior differences between
    new and returning users across applications.

Parameters:
    - limit (int, optional): Maximum number of applications to analyze (default: 50)
    - app_name (str, optional): Filter by specific application name
    - new_user_days (int, optional): Days to consider a user as "new" (default: 30)
    - sort_by (str, optional): Sort field (total_users, new_users, returning_users)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with new vs returning user analysis and insights

Examples:
    Basic usage:
    Input: {}
    Output: New vs returning user analysis for all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "new_user_days": 14}
    Output: Chrome new vs returning users with 14-day new user window

Database Tables Used:
    - app_usage: For user activity and first-time usage tracking

Related Tools:
    - growth_trend_analysis: Analyze overall user growth patterns
    - churn_rate_analysis: Compare with retention metrics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query
from shared.date_utils import days_ago

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def new_vs_returning_users(
    limit: int = 50,
    app_name: Optional[str] = None,
    new_user_days: int = 30,
    sort_by: str = "total_users",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Analyze new vs returning user patterns.
    
    Args:
        limit: Maximum number of applications to analyze (default: 50, max: 200)
        app_name: Filter by specific application name
        new_user_days: Days to consider a user as "new" (default: 30, max: 365)
        sort_by: Field to sort by (total_users, new_users, returning_users, retention_rate)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing new vs returning user analysis and insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing new vs returning users {filter_desc}, new user window: {new_user_days} days, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        
        if new_user_days < 1 or new_user_days > 365:
            raise ValueError("new_user_days must be between 1 and 365")
        
        valid_sort_fields = ['total_users', 'new_users', 'returning_users', 'retention_rate']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Calculate new user cutoff date
        new_user_cutoff_date = days_ago(new_user_days)
        
        if ctx:
            ctx.debug(f"New user cutoff date: {new_user_cutoff_date}")
            ctx.report_progress(25, 100, "Analyzing new vs returning user patterns...")
        
        # Build query to analyze new vs returning users
        base_query = """
        WITH user_first_activity AS (
            SELECT 
                application_name,
                user,
                MIN(log_date) as first_activity_date,
                COUNT(*) as total_sessions,
                SUM(duration_seconds) as total_seconds,
                MAX(log_date) as last_activity_date
            FROM app_usage
            WHERE duration_seconds > 0
            GROUP BY application_name, user
        ),
        user_categorization AS (
            SELECT 
                application_name,
                user,
                first_activity_date,
                total_sessions,
                total_seconds,
                last_activity_date,
                CASE 
                    WHEN first_activity_date >= ? THEN 'new'
                    ELSE 'returning'
                END as user_type,
                CAST((julianday(last_activity_date) - julianday(first_activity_date)) AS INTEGER) as days_active
            FROM user_first_activity
        ),
        app_user_analysis AS (
            SELECT 
                application_name,
                COUNT(DISTINCT user) as total_users,
                COUNT(DISTINCT CASE WHEN user_type = 'new' THEN user END) as new_users,
                COUNT(DISTINCT CASE WHEN user_type = 'returning' THEN user END) as returning_users,
                SUM(CASE WHEN user_type = 'new' THEN total_sessions ELSE 0 END) as new_user_sessions,
                SUM(CASE WHEN user_type = 'returning' THEN total_sessions ELSE 0 END) as returning_user_sessions,
                SUM(CASE WHEN user_type = 'new' THEN total_seconds ELSE 0 END) as new_user_seconds,
                SUM(CASE WHEN user_type = 'returning' THEN total_seconds ELSE 0 END) as returning_user_seconds,
                AVG(CASE WHEN user_type = 'new' THEN total_sessions END) as avg_sessions_new,
                AVG(CASE WHEN user_type = 'returning' THEN total_sessions END) as avg_sessions_returning,
                AVG(CASE WHEN user_type = 'new' THEN days_active END) as avg_days_active_new,
                AVG(CASE WHEN user_type = 'returning' THEN days_active END) as avg_days_active_returning
            FROM user_categorization
            GROUP BY application_name
            HAVING total_users >= 10
        )
        SELECT 
            application_name,
            total_users,
            new_users,
            returning_users,
            new_user_sessions,
            returning_user_sessions,
            new_user_seconds,
            returning_user_seconds,
            ROUND(avg_sessions_new, 2) as avg_sessions_new,
            ROUND(avg_sessions_returning, 2) as avg_sessions_returning,
            ROUND(avg_days_active_new, 2) as avg_days_active_new,
            ROUND(avg_days_active_returning, 2) as avg_days_active_returning,
            ROUND((CAST(returning_users AS FLOAT) / total_users * 100), 2) as retention_rate,
            ROUND((CAST(new_users AS FLOAT) / total_users * 100), 2) as new_user_rate
        FROM app_user_analysis
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'total_users': 'total_users',
            'new_users': 'new_users',
            'returning_users': 'returning_users',
            'retention_rate': 'retention_rate'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by=order_clause,
            limit=limit
        )
        
        # Add new user cutoff date as first parameter
        params = (new_user_cutoff_date,) + params
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing new vs returning user analysis...")
        
        # Format response
        response_data = {
            "tool": "new_vs_returning_users",
            "description": "New vs returning user analysis",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "new_user_days": new_user_days,
                "new_user_cutoff_date": new_user_cutoff_date,
                "app_name_filter": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "user_analysis": []
        }
        
        # Process user analysis data
        total_users_analyzed = 0
        total_new_users = 0
        total_returning_users = 0
        total_new_sessions = 0
        total_returning_sessions = 0
        total_new_hours = 0
        total_returning_hours = 0
        
        high_retention_apps = 0
        moderate_retention_apps = 0
        low_retention_apps = 0
        
        for record in result.data:
            new_user_hours = (record["new_user_seconds"] or 0) / 3600
            returning_user_hours = (record["returning_user_seconds"] or 0) / 3600
            retention_rate = record["retention_rate"] or 0
            new_user_rate = record["new_user_rate"] or 0
            
            total_users_analyzed += record["total_users"]
            total_new_users += record["new_users"]
            total_returning_users += record["returning_users"]
            total_new_sessions += record["new_user_sessions"]
            total_returning_sessions += record["returning_user_sessions"]
            total_new_hours += new_user_hours
            total_returning_hours += returning_user_hours
            
            # Categorize retention performance
            if retention_rate >= 70:
                high_retention_apps += 1
                retention_category = "high_retention"
            elif retention_rate >= 40:
                moderate_retention_apps += 1
                retention_category = "moderate_retention"
            else:
                low_retention_apps += 1
                retention_category = "low_retention"
            
            # Generate insights and recommendations
            insights = []
            recommendations = []
            
            if retention_rate >= 80:
                insights.append("Excellent user retention - strong product-market fit")
                recommendations.append("Focus on scaling acquisition while maintaining quality")
            elif retention_rate >= 60:
                insights.append("Good user retention - solid foundation")
                recommendations.append("Optimize onboarding to improve new user experience")
            elif retention_rate >= 30:
                insights.append("Moderate retention - room for improvement")
                recommendations.append("Investigate user drop-off points and improve engagement")
            else:
                insights.append("Low retention - critical issue")
                recommendations.append("Urgent: Analyze user feedback and improve core value proposition")
            
            # Compare new vs returning user engagement
            if record["avg_sessions_new"] and record["avg_sessions_returning"]:
                if record["avg_sessions_returning"] > record["avg_sessions_new"] * 2:
                    insights.append("Returning users much more engaged than new users")
                    recommendations.append("Improve new user onboarding and early engagement")
                elif record["avg_sessions_new"] > record["avg_sessions_returning"]:
                    insights.append("New users more active than returning users - unusual pattern")
                    recommendations.append("Investigate why returning users are less active")
            
            if new_user_rate > 70:
                insights.append("High proportion of new users - rapid growth phase")
                recommendations.append("Focus on retention strategies to convert new users")
            elif new_user_rate < 20:
                insights.append("Low new user acquisition - mature or declining app")
                recommendations.append("Invest in user acquisition and marketing")
            
            user_info = {
                "application_name": record["application_name"],
                "user_metrics": {
                    "total_users": record["total_users"],
                    "new_users": record["new_users"],
                    "returning_users": record["returning_users"],
                    "retention_rate_percentage": retention_rate,
                    "new_user_rate_percentage": new_user_rate,
                    "retention_category": retention_category
                },
                "engagement_comparison": {
                    "new_user_engagement": {
                        "total_sessions": record["new_user_sessions"],
                        "total_hours": round(new_user_hours, 2),
                        "avg_sessions_per_user": record["avg_sessions_new"],
                        "avg_days_active": record["avg_days_active_new"]
                    },
                    "returning_user_engagement": {
                        "total_sessions": record["returning_user_sessions"],
                        "total_hours": round(returning_user_hours, 2),
                        "avg_sessions_per_user": record["avg_sessions_returning"],
                        "avg_days_active": record["avg_days_active_returning"]
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
            response_data["user_analysis"].append(user_info)
        
        # Calculate overall statistics
        overall_retention_rate = (total_returning_users / total_users_analyzed * 100) if total_users_analyzed > 0 else 0
        overall_new_user_rate = (total_new_users / total_users_analyzed * 100) if total_users_analyzed > 0 else 0
        
        # Add summary statistics
        response_data["summary"] = {
            "total_users_analyzed": total_users_analyzed,
            "total_new_users": total_new_users,
            "total_returning_users": total_returning_users,
            "overall_retention_rate_percentage": round(overall_retention_rate, 2),
            "overall_new_user_rate_percentage": round(overall_new_user_rate, 2),
            "retention_distribution": {
                "high_retention_apps": high_retention_apps,
                "moderate_retention_apps": moderate_retention_apps,
                "low_retention_apps": low_retention_apps
            },
            "engagement_totals": {
                "new_user_sessions": total_new_sessions,
                "returning_user_sessions": total_returning_sessions,
                "new_user_hours": round(total_new_hours, 2),
                "returning_user_hours": round(total_returning_hours, 2)
            }
        }
        
        # Add market insights
        response_data["market_insights"] = {
            "best_retention_apps": [
                {
                    "app": app["application_name"],
                    "retention_rate": app["user_metrics"]["retention_rate_percentage"],
                    "total_users": app["user_metrics"]["total_users"]
                }
                for app in sorted(response_data["user_analysis"], 
                                key=lambda x: x["user_metrics"]["retention_rate_percentage"], reverse=True)
            ][:5],
            "fastest_growing_apps": [
                {
                    "app": app["application_name"],
                    "new_user_rate": app["user_metrics"]["new_user_rate_percentage"],
                    "new_users": app["user_metrics"]["new_users"]
                }
                for app in sorted(response_data["user_analysis"], 
                                key=lambda x: x["user_metrics"]["new_user_rate_percentage"], reverse=True)
            ][:5],
            "engagement_leaders": [
                {
                    "app": app["application_name"],
                    "returning_user_avg_sessions": app["engagement_comparison"]["returning_user_engagement"]["avg_sessions_per_user"],
                    "retention_rate": app["user_metrics"]["retention_rate_percentage"]
                }
                for app in sorted(response_data["user_analysis"], 
                                key=lambda x: x["engagement_comparison"]["returning_user_engagement"]["avg_sessions_per_user"] or 0, reverse=True)
            ][:5]
        }
        
        # Add strategic recommendations
        response_data["strategic_recommendations"] = {
            "acquisition_focus": [
                "Apps with high retention but low new user rates need acquisition investment",
                "Apps with high new user rates should focus on retention optimization",
                "Balance acquisition spend based on retention performance"
            ],
            "retention_strategies": [
                "Improve onboarding for apps with low new user engagement",
                "Implement re-engagement campaigns for apps with declining returning users",
                "Study high-retention apps to identify best practices"
            ],
            "product_development": [
                "Focus on features that increase returning user engagement",
                "Optimize first-time user experience based on successful patterns",
                "Implement user feedback loops to understand retention drivers"
            ]
        }
        
        if ctx:
            ctx.report_progress(100, 100, "New vs returning user analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} apps, {overall_retention_rate:.1f}% overall retention")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in new_vs_returning_users: {e}")
        if ctx:
            ctx.error(f"Failed to analyze new vs returning users: {e}")
        
        return {
            "tool": "new_vs_returning_users",
            "error": str(e),
            "message": "Failed to analyze new vs returning users"
        }
