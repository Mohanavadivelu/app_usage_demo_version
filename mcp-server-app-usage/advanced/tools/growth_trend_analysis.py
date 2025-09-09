"""
Tool: Growth Trend Analysis
Category: Advanced
Feature ID: 43

Description:
    Analyze user growth trends over time. This tool tracks how user bases
    are growing or declining across applications, providing insights into
    adoption patterns and growth trajectories.

Parameters:
    - limit (int, optional): Maximum number of applications to analyze (default: 50)
    - time_period_days (int, optional): Time period for trend analysis in days (default: 90)
    - app_name (str, optional): Filter by specific application name
    - sort_by (str, optional): Sort field (growth_rate, new_users, total_users)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with growth trend analysis and insights

Examples:
    Basic usage:
    Input: {}
    Output: Growth trend analysis for all applications over 90 days

    Specific app analysis:
    Input: {"app_name": "Chrome", "time_period_days": 180}
    Output: Chrome growth trend analysis over 180 days

Database Tables Used:
    - app_usage: For user activity and growth tracking

Related Tools:
    - new_vs_returning_users: Analyze user acquisition patterns
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
async def growth_trend_analysis(
    limit: int = 50,
    time_period_days: int = 90,
    app_name: Optional[str] = None,
    sort_by: str = "growth_rate",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Analyze user growth trends over time.
    
    Args:
        limit: Maximum number of applications to analyze (default: 50, max: 200)
        time_period_days: Time period for trend analysis in days (default: 90, max: 365)
        app_name: Filter by specific application name
        sort_by: Field to sort by (growth_rate, new_users, total_users, growth_velocity)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing growth trend analysis and insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing growth trends {filter_desc}, period: {time_period_days} days, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        
        if time_period_days < 7 or time_period_days > 365:
            raise ValueError("time_period_days must be between 7 and 365")
        
        valid_sort_fields = ['growth_rate', 'new_users', 'total_users', 'growth_velocity']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Calculate date boundaries
        analysis_start_date = days_ago(time_period_days)
        midpoint_date = days_ago(time_period_days // 2)
        current_date = days_ago(0)
        
        if ctx:
            ctx.debug(f"Growth analysis period: {analysis_start_date} to {current_date}")
            ctx.report_progress(25, 100, "Calculating growth trends...")
        
        # Build query to analyze growth trends
        base_query = """
        WITH user_first_activity AS (
            SELECT 
                application_name,
                user,
                MIN(log_date) as first_activity_date
            FROM app_usage
            WHERE log_date >= ?
            GROUP BY application_name, user
        ),
        period_analysis AS (
            SELECT 
                application_name,
                COUNT(DISTINCT user) as total_users,
                COUNT(DISTINCT CASE WHEN first_activity_date >= ? THEN user END) as recent_new_users,
                COUNT(DISTINCT CASE WHEN first_activity_date < ? THEN user END) as early_new_users,
                MIN(first_activity_date) as first_user_date,
                MAX(first_activity_date) as latest_user_date
            FROM user_first_activity
            GROUP BY application_name
            HAVING total_users >= 10
        ),
        growth_calculations AS (
            SELECT 
                application_name,
                total_users,
                recent_new_users,
                early_new_users,
                first_user_date,
                latest_user_date,
                CASE 
                    WHEN early_new_users > 0 THEN 
                        ROUND(((CAST(recent_new_users AS FLOAT) - early_new_users) / early_new_users * 100), 2)
                    ELSE 100.0
                END as growth_rate,
                ROUND((CAST(recent_new_users AS FLOAT) / (? / 2.0)), 2) as growth_velocity
            FROM period_analysis
        )
        SELECT 
            application_name,
            total_users,
            recent_new_users,
            early_new_users,
            growth_rate,
            growth_velocity,
            first_user_date,
            latest_user_date,
            CASE 
                WHEN growth_rate > 50 THEN 'high_growth'
                WHEN growth_rate > 20 THEN 'moderate_growth'
                WHEN growth_rate > 0 THEN 'slow_growth'
                WHEN growth_rate = 0 THEN 'stagnant'
                ELSE 'declining'
            END as growth_category
        FROM growth_calculations
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'growth_rate': 'growth_rate',
            'new_users': 'recent_new_users',
            'total_users': 'total_users',
            'growth_velocity': 'growth_velocity'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            order_by=order_clause,
            limit=limit
        )
        
        # Add date parameters at the beginning
        params = (analysis_start_date, midpoint_date, midpoint_date, time_period_days) + params
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing growth analysis...")
        
        # Format response
        response_data = {
            "tool": "growth_trend_analysis",
            "description": "User growth trend analysis",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "time_period_days": time_period_days,
                "analysis_start_date": analysis_start_date,
                "midpoint_date": midpoint_date,
                "current_date": current_date,
                "app_name_filter": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "growth_analysis": []
        }
        
        # Process growth data
        total_users_analyzed = 0
        total_new_users = 0
        high_growth_apps = 0
        moderate_growth_apps = 0
        slow_growth_apps = 0
        stagnant_apps = 0
        declining_apps = 0
        
        for record in result.data:
            growth_rate = record["growth_rate"] or 0
            growth_velocity = record["growth_velocity"] or 0
            
            total_users_analyzed += record["total_users"]
            total_new_users += record["recent_new_users"]
            
            # Count by growth category
            category = record["growth_category"]
            if category == 'high_growth':
                high_growth_apps += 1
            elif category == 'moderate_growth':
                moderate_growth_apps += 1
            elif category == 'slow_growth':
                slow_growth_apps += 1
            elif category == 'stagnant':
                stagnant_apps += 1
            else:
                declining_apps += 1
            
            # Generate insights and recommendations
            insights = []
            recommendations = []
            
            if growth_rate > 100:
                insights.append("Exceptional growth - viral adoption pattern")
                recommendations.append("Scale infrastructure to handle rapid growth")
            elif growth_rate > 50:
                insights.append("Strong growth momentum")
                recommendations.append("Invest in user retention strategies")
            elif growth_rate > 20:
                insights.append("Healthy growth trajectory")
                recommendations.append("Continue current acquisition strategies")
            elif growth_rate > 0:
                insights.append("Slow but positive growth")
                recommendations.append("Analyze and optimize user acquisition channels")
            elif growth_rate == 0:
                insights.append("User base has plateaued")
                recommendations.append("Implement growth initiatives and feature improvements")
            else:
                insights.append("Declining user base")
                recommendations.append("Urgent: Investigate user experience issues and retention problems")
            
            if growth_velocity > 5:
                insights.append("High user acquisition velocity")
            elif growth_velocity < 1:
                insights.append("Low user acquisition rate")
            
            growth_info = {
                "application_name": record["application_name"],
                "growth_metrics": {
                    "total_users": record["total_users"],
                    "recent_new_users": record["recent_new_users"],
                    "early_new_users": record["early_new_users"],
                    "growth_rate_percentage": growth_rate,
                    "growth_velocity_users_per_day": growth_velocity,
                    "growth_category": category
                },
                "timeline": {
                    "first_user_date": record["first_user_date"],
                    "latest_user_date": record["latest_user_date"],
                    "analysis_period_days": time_period_days
                },
                "insights": insights,
                "recommendations": recommendations
            }
            response_data["growth_analysis"].append(growth_info)
        
        # Calculate overall growth metrics
        overall_growth_rate = 0
        if len(result.data) > 0:
            growth_rates = [app["growth_metrics"]["growth_rate_percentage"] for app in response_data["growth_analysis"]]
            overall_growth_rate = sum(growth_rates) / len(growth_rates)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_applications_analyzed": len(result.data),
            "total_users_analyzed": total_users_analyzed,
            "total_new_users_in_period": total_new_users,
            "average_growth_rate_percentage": round(overall_growth_rate, 2),
            "growth_distribution": {
                "high_growth_apps": high_growth_apps,
                "moderate_growth_apps": moderate_growth_apps,
                "slow_growth_apps": slow_growth_apps,
                "stagnant_apps": stagnant_apps,
                "declining_apps": declining_apps
            }
        }
        
        # Add market insights
        response_data["market_insights"] = {
            "fastest_growing_apps": [
                {
                    "app": app["application_name"],
                    "growth_rate": app["growth_metrics"]["growth_rate_percentage"],
                    "new_users": app["growth_metrics"]["recent_new_users"]
                }
                for app in sorted(response_data["growth_analysis"], 
                                key=lambda x: x["growth_metrics"]["growth_rate_percentage"], reverse=True)
            ][:5],
            "highest_velocity_apps": [
                {
                    "app": app["application_name"],
                    "velocity": app["growth_metrics"]["growth_velocity_users_per_day"],
                    "category": app["growth_metrics"]["growth_category"]
                }
                for app in sorted(response_data["growth_analysis"], 
                                key=lambda x: x["growth_metrics"]["growth_velocity_users_per_day"], reverse=True)
            ][:5],
            "market_health": {
                "growth_momentum": "strong" if overall_growth_rate > 30 else "moderate" if overall_growth_rate > 10 else "weak",
                "apps_in_growth_phase": high_growth_apps + moderate_growth_apps,
                "apps_needing_attention": stagnant_apps + declining_apps,
                "market_expansion_rate": round((total_new_users / total_users_analyzed * 100), 2) if total_users_analyzed > 0 else 0
            }
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Growth trend analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} apps, {overall_growth_rate:.1f}% avg growth rate")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in growth_trend_analysis: {e}")
        if ctx:
            ctx.error(f"Failed to analyze growth trends: {e}")
        
        return {
            "tool": "growth_trend_analysis",
            "error": str(e),
            "message": "Failed to analyze growth trends"
        }
