"""
Tool: Inactive Users
Category: Advanced
Feature ID: 40

Description:
    Identify inactive users who haven't used applications recently.
    This tool helps identify users at risk of churning and those who
    may need re-engagement campaigns.

Parameters:
    - limit (int, optional): Maximum number of users to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - inactive_days (int, optional): Days since last activity to be considered inactive (default: 30)
    - sort_by (str, optional): Sort field (days_inactive, last_total_hours, last_sessions)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with inactive user analysis and re-engagement insights

Examples:
    Basic usage:
    Input: {}
    Output: Users inactive for 30+ days across all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "inactive_days": 60}
    Output: Chrome users inactive for 60+ days

Database Tables Used:
    - app_usage: For user activity tracking

Related Tools:
    - churn_rate_analysis: Analyze overall churn patterns
    - heavy_users: Compare with active user segments

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
async def inactive_users(
    limit: int = 100,
    app_name: Optional[str] = None,
    inactive_days: int = 30,
    sort_by: str = "days_inactive",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Identify inactive users who haven't used applications recently.
    
    Args:
        limit: Maximum number of users to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        inactive_days: Days since last activity to be considered inactive (default: 30, max: 365)
        sort_by: Field to sort by (days_inactive, last_total_hours, last_sessions, apps_used)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing inactive user analysis and re-engagement insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "across all applications"
            ctx.info(f"Identifying inactive users {filter_desc}, inactive threshold: {inactive_days} days, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        if inactive_days < 1 or inactive_days > 365:
            raise ValueError("inactive_days must be between 1 and 365")
        
        valid_sort_fields = ['days_inactive', 'last_total_hours', 'last_sessions', 'apps_used']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Calculate cutoff date for inactive users
        inactive_cutoff_date = days_ago(inactive_days)
        
        if ctx:
            ctx.debug(f"Inactive cutoff date: {inactive_cutoff_date}")
            ctx.report_progress(25, 100, "Identifying inactive users...")
        
        # Build query to identify inactive users
        base_query = """
        WITH user_last_activity AS (
            SELECT 
                user,
                application_name,
                MAX(log_date) as last_activity_date,
                COUNT(*) as total_sessions,
                SUM(duration_seconds) as total_seconds,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(log_date) as first_activity_date
            FROM app_usage
            WHERE duration_seconds > 0
            GROUP BY user, application_name
        ),
        inactive_analysis AS (
            SELECT 
                user,
                CASE WHEN ? IS NULL THEN 'Multiple Apps' ELSE application_name END as application_context,
                last_activity_date,
                total_sessions,
                total_seconds,
                avg_session_seconds,
                first_activity_date,
                CAST((julianday('now') - julianday(last_activity_date)) AS INTEGER) as days_inactive,
                COUNT(DISTINCT application_name) as apps_used
            FROM user_last_activity
            WHERE last_activity_date < ?
            GROUP BY user
        )
        SELECT 
            user,
            application_context,
            last_activity_date,
            days_inactive,
            total_sessions,
            total_seconds,
            avg_session_seconds,
            first_activity_date,
            apps_used,
            CASE 
                WHEN days_inactive > 180 THEN 'long_term_inactive'
                WHEN days_inactive > 90 THEN 'medium_term_inactive'
                WHEN days_inactive > 60 THEN 'short_term_inactive'
                ELSE 'recently_inactive'
            END as inactivity_category
        FROM inactive_analysis
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'days_inactive': 'days_inactive',
            'last_total_hours': 'total_seconds',
            'last_sessions': 'total_sessions',
            'apps_used': 'apps_used'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by=order_clause,
            limit=limit
        )
        
        # Add parameters for the CTE
        params = (app_name, inactive_cutoff_date) + params
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} inactive users in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing inactive user analysis...")
        
        # Format response
        response_data = {
            "tool": "inactive_users",
            "description": "Inactive user identification and re-engagement analysis",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "inactive_days_threshold": inactive_days,
                "inactive_cutoff_date": inactive_cutoff_date,
                "app_name_filter": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "inactive_users": []
        }
        
        # Process inactive user data
        total_inactive_users = len(result.data)
        inactivity_categories = {
            "recently_inactive": 0,
            "short_term_inactive": 0, 
            "medium_term_inactive": 0,
            "long_term_inactive": 0
        }
        total_lost_hours = 0
        total_lost_sessions = 0
        
        for record in result.data:
            total_seconds = record["total_seconds"] or 0
            total_hours = total_seconds / 3600
            avg_session_seconds = record["avg_session_seconds"] or 0
            avg_session_minutes = avg_session_seconds / 60
            days_inactive = record["days_inactive"] or 0
            
            total_lost_hours += total_hours
            total_lost_sessions += record["total_sessions"]
            
            # Count by inactivity category
            category = record["inactivity_category"]
            inactivity_categories[category] += 1
            
            # Generate re-engagement insights and recommendations
            insights = []
            recommendations = []
            
            if days_inactive > 180:
                insights.append("Long-term inactive - high churn risk")
                recommendations.append("Aggressive re-engagement campaign with incentives")
                recommendations.append("Survey to understand reasons for leaving")
            elif days_inactive > 90:
                insights.append("Medium-term inactive - moderate churn risk")
                recommendations.append("Targeted email campaign highlighting new features")
                recommendations.append("Personalized content based on past usage")
            elif days_inactive > 60:
                insights.append("Short-term inactive - early intervention opportunity")
                recommendations.append("Gentle reminder notifications")
                recommendations.append("Feature tutorials and tips")
            else:
                insights.append("Recently inactive - good re-engagement potential")
                recommendations.append("Push notifications about relevant updates")
                recommendations.append("Social proof and community engagement")
            
            # Analyze past engagement level
            if total_hours > 100:
                insights.append("Was a heavy user - high value recovery target")
                recommendations.append("Priority re-engagement with personal outreach")
            elif total_hours > 20:
                insights.append("Had moderate engagement")
                recommendations.append("Standard re-engagement workflow")
            else:
                insights.append("Had low engagement - may need different approach")
                recommendations.append("Focus on onboarding and value demonstration")
            
            if record["apps_used"] > 3:
                insights.append("Multi-app user - ecosystem value")
                recommendations.append("Cross-app re-engagement strategy")
            
            # Calculate user lifetime value indicators
            days_active = 0
            if record["first_activity_date"] and record["last_activity_date"]:
                days_active = (record["last_activity_date"] != record["first_activity_date"])
            
            user_info = {
                "user": record["user"],
                "application_context": record["application_context"],
                "inactivity_metrics": {
                    "days_inactive": days_inactive,
                    "last_activity_date": record["last_activity_date"],
                    "inactivity_category": category
                },
                "past_engagement": {
                    "total_hours": round(total_hours, 2),
                    "total_sessions": record["total_sessions"],
                    "apps_used": record["apps_used"],
                    "average_session_minutes": round(avg_session_minutes, 2),
                    "first_activity_date": record["first_activity_date"],
                    "days_active": days_active
                },
                "insights": insights,
                "recommendations": recommendations
            }
            response_data["inactive_users"].append(user_info)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_inactive_users": total_inactive_users,
            "total_lost_usage_hours": round(total_lost_hours, 2),
            "total_lost_sessions": total_lost_sessions,
            "average_lost_hours_per_user": round(total_lost_hours / total_inactive_users, 2) if total_inactive_users > 0 else 0,
            "inactivity_distribution": inactivity_categories
        }
        
        # Add re-engagement strategy insights
        response_data["reengagement_strategy"] = {
            "priority_segments": [
                {
                    "segment": "High-value inactive users",
                    "criteria": "Previously heavy users (>100h) inactive >30 days",
                    "count": len([u for u in response_data["inactive_users"] 
                                if u["past_engagement"]["total_hours"] > 100]),
                    "approach": "Personal outreach with premium incentives"
                },
                {
                    "segment": "Multi-app inactive users", 
                    "criteria": "Used 3+ apps, inactive >60 days",
                    "count": len([u for u in response_data["inactive_users"] 
                                if u["past_engagement"]["apps_used"] > 3 and u["inactivity_metrics"]["days_inactive"] > 60]),
                    "approach": "Cross-platform re-engagement campaign"
                },
                {
                    "segment": "Recently inactive users",
                    "criteria": "Inactive 30-60 days",
                    "count": inactivity_categories["recently_inactive"],
                    "approach": "Gentle nudges and feature highlights"
                }
            ],
            "campaign_recommendations": [
                "Segment users by past engagement level",
                "Personalize messaging based on previous app usage",
                "Use progressive re-engagement (start gentle, increase intensity)",
                "A/B test different incentive types",
                "Track re-activation rates by segment"
            ]
        }
        
        # Add business impact analysis
        response_data["business_impact"] = {
            "churn_risk_analysis": {
                "high_risk_users": inactivity_categories["long_term_inactive"] + inactivity_categories["medium_term_inactive"],
                "moderate_risk_users": inactivity_categories["short_term_inactive"],
                "low_risk_users": inactivity_categories["recently_inactive"],
                "estimated_revenue_at_risk": "Calculate based on user LTV and segment sizes"
            },
            "recovery_potential": {
                "high_potential": len([u for u in response_data["inactive_users"] 
                                     if u["past_engagement"]["total_hours"] > 50 and u["inactivity_metrics"]["days_inactive"] < 90]),
                "medium_potential": len([u for u in response_data["inactive_users"] 
                                       if u["past_engagement"]["total_hours"] > 10 and u["inactivity_metrics"]["days_inactive"] < 180]),
                "low_potential": len([u for u in response_data["inactive_users"] 
                                    if u["inactivity_metrics"]["days_inactive"] > 180])
            }
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Inactive user analysis complete")
            ctx.info(f"Analysis complete: {total_inactive_users} inactive users, {total_lost_hours:.1f}h lost usage")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in inactive_users: {e}")
        if ctx:
            ctx.error(f"Failed to identify inactive users: {e}")
        
        return {
            "tool": "inactive_users",
            "error": str(e),
            "message": "Failed to identify inactive users"
        }
