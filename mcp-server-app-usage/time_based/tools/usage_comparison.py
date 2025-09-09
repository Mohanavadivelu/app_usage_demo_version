"""
Tool: Usage Comparison
Category: Time Based
Feature ID: 56

Description:
    Compare usage between date ranges - analyzes and compares application usage
    metrics between two different time periods to identify trends and changes.

Parameters:
    - period1_start (str, required): Start date for first period (YYYY-MM-DD format)
    - period1_end (str, required): End date for first period (YYYY-MM-DD format)
    - period2_start (str, required): Start date for second period (YYYY-MM-DD format)
    - period2_end (str, required): End date for second period (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of applications to compare (default: 100)

Returns:
    - Compare usage between date ranges with detailed analytics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from shared.database_utils import execute_analytics_query, validate_parameters
from server_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def usage_comparison(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    limit: Optional[int] = 100
) -> str:
    """
    Compare usage between two date ranges.
    
    Analyzes and compares application usage metrics between two different
    time periods to identify trends, growth, and changes in user behavior.
    
    Args:
        period1_start: Start date for first period (YYYY-MM-DD format, required)
        period1_end: End date for first period (YYYY-MM-DD format, required)
        period2_start: Start date for second period (YYYY-MM-DD format, required)
        period2_end: End date for second period (YYYY-MM-DD format, required)
        limit: Maximum number of applications to compare (default: 100)
    
    Returns:
        JSON string containing usage comparison with detailed analytics
    """
    try:
        # Validate required parameters
        if not all([period1_start, period1_end, period2_start, period2_end]):
            raise ValueError("All period dates are required (period1_start, period1_end, period2_start, period2_end)")
        
        # Validate date formats
        date_params = [
            ("period1_start", period1_start),
            ("period1_end", period1_end),
            ("period2_start", period2_start),
            ("period2_end", period2_end)
        ]
        
        for param_name, date_value in date_params:
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"{param_name} must be in YYYY-MM-DD format")
        
        # Validate parameter constraints
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        
        # Set defaults
        limit = limit or 100
        
        # Validate date logic
        if period1_start >= period1_end:
            raise ValueError("period1_start must be before period1_end")
        if period2_start >= period2_end:
            raise ValueError("period2_start must be before period2_end")
        
        logger.info(f"Comparing usage between Period 1 ({period1_start} to {period1_end}) and Period 2 ({period2_start} to {period2_end})")
        
        # Query to compare usage between two periods
        query = """
        WITH period1_stats AS (
            SELECT 
                app_name,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY app_name
        ),
        period2_stats AS (
            SELECT 
                app_name,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY app_name
        ),
        combined_comparison AS (
            SELECT 
                COALESCE(p1.app_name, p2.app_name) as app_name,
                COALESCE(p1.unique_users, 0) as period1_users,
                COALESCE(p2.unique_users, 0) as period2_users,
                COALESCE(p1.total_sessions, 0) as period1_sessions,
                COALESCE(p2.total_sessions, 0) as period2_sessions,
                COALESCE(p1.total_duration_minutes, 0) as period1_duration,
                COALESCE(p2.total_duration_minutes, 0) as period2_duration,
                COALESCE(p1.avg_session_duration, 0) as period1_avg_session,
                COALESCE(p2.avg_session_duration, 0) as period2_avg_session,
                COALESCE(p1.active_days, 0) as period1_active_days,
                COALESCE(p2.active_days, 0) as period2_active_days
            FROM period1_stats p1
            FULL OUTER JOIN period2_stats p2 ON p1.app_name = p2.app_name
        ),
        comparison_analysis AS (
            SELECT 
                *,
                -- User change calculations
                CASE 
                    WHEN period1_users = 0 AND period2_users > 0 THEN 100.0
                    WHEN period1_users > 0 AND period2_users = 0 THEN -100.0
                    WHEN period1_users = 0 AND period2_users = 0 THEN 0.0
                    ELSE ROUND(((period2_users - period1_users) * 100.0 / period1_users), 2)
                END as user_change_percent,
                
                -- Session change calculations
                CASE 
                    WHEN period1_sessions = 0 AND period2_sessions > 0 THEN 100.0
                    WHEN period1_sessions > 0 AND period2_sessions = 0 THEN -100.0
                    WHEN period1_sessions = 0 AND period2_sessions = 0 THEN 0.0
                    ELSE ROUND(((period2_sessions - period1_sessions) * 100.0 / period1_sessions), 2)
                END as session_change_percent,
                
                -- Duration change calculations
                CASE 
                    WHEN period1_duration = 0 AND period2_duration > 0 THEN 100.0
                    WHEN period1_duration > 0 AND period2_duration = 0 THEN -100.0
                    WHEN period1_duration = 0 AND period2_duration = 0 THEN 0.0
                    ELSE ROUND(((period2_duration - period1_duration) * 100.0 / period1_duration), 2)
                END as duration_change_percent,
                
                -- Engagement change calculations
                CASE 
                    WHEN period1_avg_session = 0 AND period2_avg_session > 0 THEN 100.0
                    WHEN period1_avg_session > 0 AND period2_avg_session = 0 THEN -100.0
                    WHEN period1_avg_session = 0 AND period2_avg_session = 0 THEN 0.0
                    ELSE ROUND(((period2_avg_session - period1_avg_session) * 100.0 / period1_avg_session), 2)
                END as engagement_change_percent,
                
                -- Status classification
                CASE 
                    WHEN period1_users = 0 AND period2_users > 0 THEN 'New App'
                    WHEN period1_users > 0 AND period2_users = 0 THEN 'Discontinued'
                    WHEN period1_users > 0 AND period2_users > 0 THEN 'Continuing'
                    ELSE 'No Usage'
                END as app_status
            FROM combined_comparison
        ),
        trend_classification AS (
            SELECT 
                *,
                CASE 
                    WHEN user_change_percent >= 50 THEN 'High Growth'
                    WHEN user_change_percent >= 20 THEN 'Moderate Growth'
                    WHEN user_change_percent >= 5 THEN 'Slight Growth'
                    WHEN user_change_percent >= -5 THEN 'Stable'
                    WHEN user_change_percent >= -20 THEN 'Slight Decline'
                    WHEN user_change_percent >= -50 THEN 'Moderate Decline'
                    ELSE 'High Decline'
                END as growth_trend,
                
                CASE 
                    WHEN engagement_change_percent >= 20 THEN 'Much More Engaging'
                    WHEN engagement_change_percent >= 10 THEN 'More Engaging'
                    WHEN engagement_change_percent >= -10 THEN 'Similar Engagement'
                    WHEN engagement_change_percent >= -20 THEN 'Less Engaging'
                    ELSE 'Much Less Engaging'
                END as engagement_trend
            FROM comparison_analysis
        )
        SELECT 
            app_name,
            period1_users,
            period2_users,
            period1_sessions,
            period2_sessions,
            period1_duration,
            period2_duration,
            period1_avg_session,
            period2_avg_session,
            period1_active_days,
            period2_active_days,
            user_change_percent,
            session_change_percent,
            duration_change_percent,
            engagement_change_percent,
            app_status,
            growth_trend,
            engagement_trend
        FROM trend_classification
        WHERE app_status != 'No Usage'
        ORDER BY ABS(user_change_percent) DESC, period2_users DESC
        LIMIT ?
        """
        
        params = (period1_start, period1_end, period2_start, period2_end, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "usage_comparison",
                "status": "success",
                "message": "No usage data found for the specified periods",
                "data": {
                    "comparisons": [],
                    "total_apps_compared": 0,
                    "parameters": {
                        "period1": {"start": period1_start, "end": period1_end},
                        "period2": {"start": period2_start, "end": period2_end},
                        "limit": limit
                    }
                }
            }, indent=2)
        
        # Process results
        comparisons = []
        app_status_distribution = {}
        growth_trend_distribution = {}
        engagement_trend_distribution = {}
        
        for row in results:
            comparison_data = {
                "app_name": row[0],
                "period1_metrics": {
                    "unique_users": row[1],
                    "total_sessions": row[3],
                    "total_duration_minutes": row[5],
                    "avg_session_duration": row[7],
                    "active_days": row[9]
                },
                "period2_metrics": {
                    "unique_users": row[2],
                    "total_sessions": row[4],
                    "total_duration_minutes": row[6],
                    "avg_session_duration": row[8],
                    "active_days": row[10]
                },
                "change_analysis": {
                    "user_change_percent": row[11],
                    "session_change_percent": row[12],
                    "duration_change_percent": row[13],
                    "engagement_change_percent": row[14]
                },
                "classification": {
                    "app_status": row[15],
                    "growth_trend": row[16],
                    "engagement_trend": row[17]
                }
            }
            comparisons.append(comparison_data)
            
            # Update distributions
            app_status = row[15]
            growth_trend = row[16]
            engagement_trend = row[17]
            
            app_status_distribution[app_status] = app_status_distribution.get(app_status, 0) + 1
            growth_trend_distribution[growth_trend] = growth_trend_distribution.get(growth_trend, 0) + 1
            engagement_trend_distribution[engagement_trend] = engagement_trend_distribution.get(engagement_trend, 0) + 1
        
        # Calculate summary statistics
        if comparisons:
            total_apps = len(comparisons)
            
            # Period totals
            period1_total_users = sum(comp["period1_metrics"]["unique_users"] for comp in comparisons)
            period2_total_users = sum(comp["period2_metrics"]["unique_users"] for comp in comparisons)
            period1_total_sessions = sum(comp["period1_metrics"]["total_sessions"] for comp in comparisons)
            period2_total_sessions = sum(comp["period2_metrics"]["total_sessions"] for comp in comparisons)
            
            # Overall changes
            overall_user_change = round(((period2_total_users - period1_total_users) * 100.0 / period1_total_users), 2) if period1_total_users > 0 else 0
            overall_session_change = round(((period2_total_sessions - period1_total_sessions) * 100.0 / period1_total_sessions), 2) if period1_total_sessions > 0 else 0
            
            # Find top performers
            highest_growth_app = max(comparisons, key=lambda x: x["change_analysis"]["user_change_percent"])
            highest_decline_app = min(comparisons, key=lambda x: x["change_analysis"]["user_change_percent"])
            most_engaging_app = max(comparisons, key=lambda x: x["change_analysis"]["engagement_change_percent"])
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if comparisons:
            insights.append(f"Compared {total_apps} applications between two periods")
            insights.append(f"Overall user change: {overall_user_change}% ({period1_total_users} → {period2_total_users})")
            insights.append(f"Overall session change: {overall_session_change}% ({period1_total_sessions} → {period2_total_sessions})")
            insights.append(f"Highest growth: {highest_growth_app['app_name']} (+{highest_growth_app['change_analysis']['user_change_percent']}% users)")
            insights.append(f"Highest decline: {highest_decline_app['app_name']} ({highest_decline_app['change_analysis']['user_change_percent']}% users)")
            insights.append(f"Most improved engagement: {most_engaging_app['app_name']} (+{most_engaging_app['change_analysis']['engagement_change_percent']}% session duration)")
            
            # Status insights
            new_apps = app_status_distribution.get('New App', 0)
            discontinued_apps = app_status_distribution.get('Discontinued', 0)
            continuing_apps = app_status_distribution.get('Continuing', 0)
            
            if new_apps > 0:
                insights.append(f"{new_apps} new applications introduced in period 2")
            if discontinued_apps > 0:
                insights.append(f"{discontinued_apps} applications discontinued from period 1")
            
            # Growth trend insights
            high_growth = growth_trend_distribution.get('High Growth', 0)
            high_decline = growth_trend_distribution.get('High Decline', 0)
            
            if high_growth > 0:
                insights.append(f"{high_growth} applications show high growth (50%+ user increase)")
            if high_decline > 0:
                insights.append(f"{high_decline} applications show high decline (50%+ user decrease)")
            
            # Recommendations
            if overall_user_change > 10:
                recommendations.append("Capitalize on overall growth momentum with expanded marketing")
                recommendations.append("Ensure infrastructure can handle increased user load")
            elif overall_user_change < -10:
                recommendations.append("Investigate causes of overall user decline")
                recommendations.append("Implement user retention and re-engagement strategies")
            
            if high_growth > 0:
                recommendations.append("Study high-growth apps to identify success factors")
                recommendations.append("Apply successful strategies to other applications")
            
            if high_decline > 0:
                recommendations.append("Prioritize improvement efforts for declining applications")
                recommendations.append("Consider sunsetting consistently declining apps")
            
            if new_apps > 0:
                recommendations.append("Monitor new app adoption patterns and optimize onboarding")
            
            recommendations.append("Use period comparison data for strategic planning and resource allocation")
            recommendations.append("Set up regular period comparisons to track long-term trends")
        
        response_data = {
            "tool": "usage_comparison",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "comparisons": comparisons,
                "summary": {
                    "total_apps_compared": len(comparisons),
                    "comparison_periods": {
                        "period1": {"start": period1_start, "end": period1_end},
                        "period2": {"start": period2_start, "end": period2_end}
                    },
                    "parameters_used": {
                        "limit": limit
                    },
                    "overall_changes": {
                        "user_change_percent": overall_user_change if comparisons else 0,
                        "session_change_percent": overall_session_change if comparisons else 0,
                        "period1_total_users": period1_total_users if comparisons else 0,
                        "period2_total_users": period2_total_users if comparisons else 0,
                        "period1_total_sessions": period1_total_sessions if comparisons else 0,
                        "period2_total_sessions": period2_total_sessions if comparisons else 0
                    },
                    "distributions": {
                        "app_status": app_status_distribution,
                        "growth_trends": growth_trend_distribution,
                        "engagement_trends": engagement_trend_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully compared usage for {len(comparisons)} applications between two periods")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in usage_comparison: {e}")
        return json.dumps({
            "tool": "usage_comparison",
            "status": "error",
            "error": str(e),
            "message": "Failed to compare usage between periods"
        }, indent=2)
