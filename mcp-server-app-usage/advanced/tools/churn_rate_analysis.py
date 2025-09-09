"""
Tool: Churn Rate Analysis
Category: Advanced
Feature ID: 41

Description:
    Calculate application churn rates. This tool analyzes user retention
    and churn patterns across applications, helping identify which apps
    are losing users and at what rate.

Parameters:
    - limit (int, optional): Maximum number of applications to analyze (default: 50)
    - time_period_days (int, optional): Time period for churn analysis in days (default: 30)
    - app_name (str, optional): Filter by specific application name
    - sort_by (str, optional): Sort field (churn_rate, total_users, churned_users)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with churn rate analysis and insights

Examples:
    Basic usage:
    Input: {}
    Output: Churn rate analysis for all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "time_period_days": 60}
    Output: Chrome churn rate analysis over 60 days

Database Tables Used:
    - app_usage: For user activity tracking

Related Tools:
    - inactive_users: Identify inactive users
    - new_vs_returning_users: Analyze user retention patterns

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
async def churn_rate_analysis(
    limit: int = 50,
    time_period_days: int = 30,
    app_name: Optional[str] = None,
    sort_by: str = "churn_rate",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Calculate application churn rates.
    
    Args:
        limit: Maximum number of applications to analyze (default: 50, max: 200)
        time_period_days: Time period for churn analysis in days (default: 30, max: 365)
        app_name: Filter by specific application name
        sort_by: Field to sort by (churn_rate, total_users, churned_users, active_users)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing churn rate analysis and insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing churn rates {filter_desc}, period: {time_period_days} days, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        
        if time_period_days < 1 or time_period_days > 365:
            raise ValueError("time_period_days must be between 1 and 365")
        
        valid_sort_fields = ['churn_rate', 'total_users', 'churned_users', 'active_users']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Calculate date boundaries
        analysis_start_date = days_ago(time_period_days * 2)  # Look back twice the period for baseline
        churn_cutoff_date = days_ago(time_period_days)
        
        if ctx:
            ctx.debug(f"Analysis period: {analysis_start_date} to {churn_cutoff_date}")
            ctx.report_progress(25, 100, "Calculating churn rates...")
        
        # Build query to analyze churn rates
        base_query = """
        WITH user_activity AS (
            SELECT 
                application_name,
                user,
                MIN(log_date) as first_seen,
                MAX(log_date) as last_seen,
                COUNT(*) as total_sessions
            FROM app_usage
            WHERE log_date >= ?
            GROUP BY application_name, user
        ),
        app_churn_analysis AS (
            SELECT 
                application_name,
                COUNT(DISTINCT user) as total_users,
                COUNT(DISTINCT CASE WHEN last_seen < ? THEN user END) as churned_users,
                COUNT(DISTINCT CASE WHEN last_seen >= ? THEN user END) as active_users,
                AVG(total_sessions) as avg_sessions_per_user,
                MIN(first_seen) as app_first_activity,
                MAX(last_seen) as app_last_activity
            FROM user_activity
            GROUP BY application_name
            HAVING total_users >= 5
        )
        SELECT 
            application_name,
            total_users,
            churned_users,
            active_users,
            ROUND((CAST(churned_users AS FLOAT) / total_users * 100), 2) as churn_rate,
            ROUND((CAST(active_users AS FLOAT) / total_users * 100), 2) as retention_rate,
            ROUND(avg_sessions_per_user, 2) as avg_sessions_per_user,
            app_first_activity,
            app_last_activity
        FROM app_churn_analysis
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'churn_rate': 'churn_rate',
            'total_users': 'total_users',
            'churned_users': 'churned_users',
            'active_users': 'active_users'
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
        params = (analysis_start_date, churn_cutoff_date, churn_cutoff_date) + params
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} applications in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing churn analysis...")
        
        # Format response
        response_data = {
            "tool": "churn_rate_analysis",
            "description": "Application churn rate analysis",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "time_period_days": time_period_days,
                "analysis_start_date": analysis_start_date,
                "churn_cutoff_date": churn_cutoff_date,
                "app_name_filter": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "churn_analysis": []
        }
        
        # Process churn data
        total_users_analyzed = 0
        total_churned_users = 0
        high_churn_apps = 0
        moderate_churn_apps = 0
        low_churn_apps = 0
        
        for record in result.data:
            churn_rate = record["churn_rate"] or 0
            retention_rate = record["retention_rate"] or 0
            
            total_users_analyzed += record["total_users"]
            total_churned_users += record["churned_users"]
            
            # Categorize churn severity
            if churn_rate > 50:
                high_churn_apps += 1
                churn_severity = "high"
            elif churn_rate > 25:
                moderate_churn_apps += 1
                churn_severity = "moderate"
            else:
                low_churn_apps += 1
                churn_severity = "low"
            
            # Generate recommendations
            recommendations = []
            if churn_rate > 60:
                recommendations.append("Critical: Immediate retention strategy needed")
            elif churn_rate > 40:
                recommendations.append("High churn detected - investigate user experience issues")
            elif churn_rate > 25:
                recommendations.append("Moderate churn - consider user engagement improvements")
            
            if record["avg_sessions_per_user"] < 5:
                recommendations.append("Low user engagement - improve onboarding")
            
            churn_info = {
                "application_name": record["application_name"],
                "churn_metrics": {
                    "total_users": record["total_users"],
                    "churned_users": record["churned_users"],
                    "active_users": record["active_users"],
                    "churn_rate_percentage": churn_rate,
                    "retention_rate_percentage": retention_rate,
                    "churn_severity": churn_severity
                },
                "engagement_metrics": {
                    "avg_sessions_per_user": record["avg_sessions_per_user"],
                    "app_first_activity": record["app_first_activity"],
                    "app_last_activity": record["app_last_activity"]
                },
                "recommendations": recommendations
            }
            response_data["churn_analysis"].append(churn_info)
        
        # Add summary statistics
        overall_churn_rate = (total_churned_users / total_users_analyzed * 100) if total_users_analyzed > 0 else 0
        
        response_data["summary"] = {
            "total_applications_analyzed": len(result.data),
            "total_users_analyzed": total_users_analyzed,
            "total_churned_users": total_churned_users,
            "overall_churn_rate_percentage": round(overall_churn_rate, 2),
            "overall_retention_rate_percentage": round(100 - overall_churn_rate, 2),
            "churn_severity_distribution": {
                "high_churn_apps": high_churn_apps,
                "moderate_churn_apps": moderate_churn_apps,
                "low_churn_apps": low_churn_apps
            }
        }
        
        # Add insights
        response_data["insights"] = {
            "apps_needing_immediate_attention": [
                app["application_name"] for app in response_data["churn_analysis"]
                if app["churn_metrics"]["churn_severity"] == "high"
            ][:5],
            "best_retention_apps": [
                {
                    "app": app["application_name"],
                    "retention_rate": app["churn_metrics"]["retention_rate_percentage"]
                }
                for app in sorted(response_data["churn_analysis"], 
                                key=lambda x: x["churn_metrics"]["retention_rate_percentage"], reverse=True)
            ][:5],
            "churn_trends": {
                "high_risk_threshold": high_churn_apps > len(result.data) * 0.3,
                "average_churn_rate": round(overall_churn_rate, 2),
                "retention_health": "good" if overall_churn_rate < 25 else "needs_attention" if overall_churn_rate < 50 else "critical"
            }
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Churn rate analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} apps, {overall_churn_rate:.1f}% overall churn rate")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in churn_rate_analysis: {e}")
        if ctx:
            ctx.error(f"Failed to analyze churn rates: {e}")
        
        return {
            "tool": "churn_rate_analysis",
            "error": str(e),
            "message": "Failed to analyze churn rates"
        }
