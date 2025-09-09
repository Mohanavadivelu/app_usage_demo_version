"""
Tool: Usage Trends
Category: Time Based
Feature ID: 57

Description:
    Weekly/monthly usage trends - analyzes usage patterns over time periods
    to identify trends, seasonality, and long-term growth patterns.

Parameters:
    - period_type (str, optional): Period type ('weekly', 'monthly') (default: 'weekly')
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - application_name (str, optional): Specific application to analyze (optional)
    - limit (int, optional): Maximum number of periods to return (default: 52)

Returns:
    - Weekly/monthly usage trends with detailed analytics

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
async def usage_trends(
    period_type: Optional[str] = "weekly",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    application_name: Optional[str] = None,
    limit: Optional[int] = 52
) -> str:
    """
    Analyze weekly/monthly usage trends.
    
    Analyzes usage patterns over time periods to identify trends,
    seasonality, and long-term growth patterns across applications.
    
    Args:
        period_type: Period type ('weekly', 'monthly') (default: 'weekly')
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        application_name: Specific application to analyze (optional)
        limit: Maximum number of periods to return (default: 52)
    
    Returns:
        JSON string containing usage trends with detailed analytics
    """
    try:
        # Validate parameters
        valid_periods = ['weekly', 'monthly']
        if period_type and period_type not in valid_periods:
            raise ValueError(f"period_type must be one of: {', '.join(valid_periods)}")
        
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        
        # Validate date formats
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("start_date must be in YYYY-MM-DD format")
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("end_date must be in YYYY-MM-DD format")
        
        # Set defaults
        period_type = period_type or "weekly"
        limit = limit or 52
        
        # Set default date range based on period type
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            if period_type == 'weekly':
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
            else:  # monthly
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 years
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            if period_type == 'weekly':
                start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=730)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing {period_type} usage trends from {start_date} to {end_date} for {application_name or 'all applications'}")
        
        # Build date grouping and application filter
        if period_type == 'weekly':
            date_group = "strftime('%Y-W%W', timestamp)"
            date_format = "strftime('%Y-W%W', timestamp)"
        else:  # monthly
            date_group = "strftime('%Y-%m', timestamp)"
            date_format = "strftime('%Y-%m', timestamp)"
        
        app_filter = ""
        params = [start_date, end_date]
        if application_name:
            app_filter = "AND app_name = ?"
            params.append(application_name)
        
        # Query to analyze usage trends
        query = f"""
        WITH period_usage AS (
            SELECT 
                {date_format} as period,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                COUNT(DISTINCT app_name) as unique_apps,
                MIN(timestamp) as period_start,
                MAX(timestamp) as period_end
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            {app_filter}
            GROUP BY {date_group}
        ),
        trend_analysis AS (
            SELECT 
                *,
                LAG(unique_users) OVER (ORDER BY period) as prev_users,
                LAG(total_sessions) OVER (ORDER BY period) as prev_sessions,
                LAG(total_duration_minutes) OVER (ORDER BY period) as prev_duration,
                ROW_NUMBER() OVER (ORDER BY period) as period_number,
                ROUND(total_duration_minutes / unique_users, 2) as avg_duration_per_user,
                ROUND(total_sessions * 1.0 / unique_users, 2) as avg_sessions_per_user
            FROM period_usage
        ),
        growth_analysis AS (
            SELECT 
                *,
                -- User growth calculations
                CASE 
                    WHEN prev_users IS NULL THEN 0
                    WHEN prev_users = 0 THEN 100
                    ELSE ROUND(((unique_users - prev_users) * 100.0 / prev_users), 2)
                END as user_growth_percent,
                
                -- Session growth calculations
                CASE 
                    WHEN prev_sessions IS NULL THEN 0
                    WHEN prev_sessions = 0 THEN 100
                    ELSE ROUND(((total_sessions - prev_sessions) * 100.0 / prev_sessions), 2)
                END as session_growth_percent,
                
                -- Duration growth calculations
                CASE 
                    WHEN prev_duration IS NULL THEN 0
                    WHEN prev_duration = 0 THEN 100
                    ELSE ROUND(((total_duration_minutes - prev_duration) * 100.0 / prev_duration), 2)
                END as duration_growth_percent,
                
                -- Activity level classification
                CASE 
                    WHEN unique_users >= 1000 THEN 'Very High Activity'
                    WHEN unique_users >= 500 THEN 'High Activity'
                    WHEN unique_users >= 200 THEN 'Moderate Activity'
                    WHEN unique_users >= 50 THEN 'Low Activity'
                    ELSE 'Very Low Activity'
                END as activity_level,
                
                -- Growth trend classification
                CASE 
                    WHEN prev_users IS NULL THEN 'No Previous Data'
                    WHEN unique_users > prev_users * 1.1 THEN 'Strong Growth'
                    WHEN unique_users > prev_users * 1.05 THEN 'Moderate Growth'
                    WHEN unique_users > prev_users * 0.95 THEN 'Stable'
                    WHEN unique_users > prev_users * 0.9 THEN 'Slight Decline'
                    ELSE 'Significant Decline'
                END as trend_direction
            FROM trend_analysis
        )
        SELECT 
            period,
            unique_users,
            total_sessions,
            total_duration_minutes,
            avg_session_duration,
            unique_apps,
            period_start,
            period_end,
            prev_users,
            prev_sessions,
            prev_duration,
            period_number,
            avg_duration_per_user,
            avg_sessions_per_user,
            user_growth_percent,
            session_growth_percent,
            duration_growth_percent,
            activity_level,
            trend_direction
        FROM growth_analysis
        ORDER BY period DESC
        LIMIT ?
        """
        
        params.append(limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "usage_trends",
                "status": "success",
                "message": "No usage trend data found for the specified period",
                "data": {
                    "trends": [],
                    "total_periods": 0,
                    "parameters": {
                        "period_type": period_type,
                        "start_date": start_date,
                        "end_date": end_date,
                        "application_name": application_name,
                        "limit": limit
                    }
                }
            }, indent=2)
        
        # Process results
        trends = []
        activity_level_distribution = {}
        trend_direction_distribution = {}
        
        for row in results:
            trend_data = {
                "period": row[0],
                "metrics": {
                    "unique_users": row[1],
                    "total_sessions": row[2],
                    "total_duration_minutes": row[3],
                    "avg_session_duration": row[4],
                    "unique_apps": row[5],
                    "avg_duration_per_user": row[12],
                    "avg_sessions_per_user": row[13]
                },
                "period_info": {
                    "period_start": row[6],
                    "period_end": row[7],
                    "period_number": row[11]
                },
                "growth_analysis": {
                    "prev_users": row[8],
                    "prev_sessions": row[9],
                    "prev_duration": row[10],
                    "user_growth_percent": row[14],
                    "session_growth_percent": row[15],
                    "duration_growth_percent": row[16]
                },
                "classification": {
                    "activity_level": row[17],
                    "trend_direction": row[18]
                }
            }
            trends.append(trend_data)
            
            # Update distributions
            activity_level = row[17]
            trend_direction = row[18]
            activity_level_distribution[activity_level] = activity_level_distribution.get(activity_level, 0) + 1
            trend_direction_distribution[trend_direction] = trend_direction_distribution.get(trend_direction, 0) + 1
        
        # Calculate summary statistics and trend analysis
        if trends:
            total_periods = len(trends)
            
            # Reverse for chronological analysis
            chronological_trends = list(reversed(trends))
            
            # Overall trend analysis
            first_period = chronological_trends[0]
            last_period = chronological_trends[-1]
            
            overall_user_growth = round(((last_period["metrics"]["unique_users"] - first_period["metrics"]["unique_users"]) * 100.0 / first_period["metrics"]["unique_users"]), 2) if first_period["metrics"]["unique_users"] > 0 else 0
            overall_session_growth = round(((last_period["metrics"]["total_sessions"] - first_period["metrics"]["total_sessions"]) * 100.0 / first_period["metrics"]["total_sessions"]), 2) if first_period["metrics"]["total_sessions"] > 0 else 0
            
            # Peak and trough analysis
            peak_users_period = max(trends, key=lambda x: x["metrics"]["unique_users"])
            trough_users_period = min(trends, key=lambda x: x["metrics"]["unique_users"])
            
            # Growth periods analysis
            growing_periods = sum(1 for trend in trends if trend["growth_analysis"]["user_growth_percent"] > 5)
            declining_periods = sum(1 for trend in trends if trend["growth_analysis"]["user_growth_percent"] < -5)
            stable_periods = total_periods - growing_periods - declining_periods
            
            # Calculate moving averages for trend smoothing
            if len(chronological_trends) >= 4:
                recent_4_avg = sum(t["metrics"]["unique_users"] for t in chronological_trends[-4:]) / 4
                previous_4_avg = sum(t["metrics"]["unique_users"] for t in chronological_trends[-8:-4]) / 4 if len(chronological_trends) >= 8 else recent_4_avg
                trend_momentum = "Accelerating" if recent_4_avg > previous_4_avg * 1.1 else "Decelerating" if recent_4_avg < previous_4_avg * 0.9 else "Steady"
            else:
                trend_momentum = "Insufficient Data"
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if trends:
            insights.append(f"Analyzed {total_periods} {period_type} periods")
            insights.append(f"Overall user growth: {overall_user_growth}% from {first_period['metrics']['unique_users']} to {last_period['metrics']['unique_users']} users")
            insights.append(f"Overall session growth: {overall_session_growth}%")
            insights.append(f"Peak period: {peak_users_period['period']} with {peak_users_period['metrics']['unique_users']} users")
            insights.append(f"Trough period: {trough_users_period['period']} with {trough_users_period['metrics']['unique_users']} users")
            insights.append(f"Trend momentum: {trend_momentum}")
            
            # Period distribution insights
            insights.append(f"Growth periods: {growing_periods}, Stable: {stable_periods}, Declining: {declining_periods}")
            
            # Activity level insights
            high_activity = activity_level_distribution.get('High Activity', 0) + activity_level_distribution.get('Very High Activity', 0)
            if high_activity > 0:
                insights.append(f"{high_activity} periods show high activity levels")
            
            # Trend direction insights
            strong_growth = trend_direction_distribution.get('Strong Growth', 0)
            significant_decline = trend_direction_distribution.get('Significant Decline', 0)
            
            if strong_growth > 0:
                insights.append(f"{strong_growth} periods show strong growth")
            if significant_decline > 0:
                insights.append(f"{significant_decline} periods show significant decline")
            
            # Recommendations
            if overall_user_growth > 20:
                recommendations.append("Capitalize on strong growth trend with increased marketing investment")
                recommendations.append("Prepare infrastructure for continued growth")
            elif overall_user_growth < -10:
                recommendations.append("Address declining trend with user retention initiatives")
                recommendations.append("Investigate root causes of user decline")
            
            if trend_momentum == "Accelerating":
                recommendations.append("Growth is accelerating - consider scaling operations")
            elif trend_momentum == "Decelerating":
                recommendations.append("Growth is slowing - review and refresh growth strategies")
            
            if growing_periods > declining_periods:
                recommendations.append("Overall positive trend - maintain current strategies")
            elif declining_periods > growing_periods:
                recommendations.append("More declining periods than growing - implement turnaround strategies")
            
            if high_activity > 0:
                recommendations.append("Leverage high-activity periods for user engagement campaigns")
            
            recommendations.append(f"Monitor {period_type} trends for early detection of pattern changes")
            recommendations.append("Use trend data for capacity planning and resource allocation")
            recommendations.append("Consider seasonal factors in trend interpretation")
        
        response_data = {
            "tool": "usage_trends",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "trends": trends,
                "summary": {
                    "total_periods": len(trends),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "period_type": period_type
                    },
                    "parameters_used": {
                        "application_name": application_name,
                        "limit": limit
                    },
                    "overall_trends": {
                        "user_growth_percent": overall_user_growth if trends else 0,
                        "session_growth_percent": overall_session_growth if trends else 0,
                        "trend_momentum": trend_momentum if trends else "No Data",
                        "growing_periods": growing_periods if trends else 0,
                        "stable_periods": stable_periods if trends else 0,
                        "declining_periods": declining_periods if trends else 0
                    },
                    "peak_trough": {
                        "peak_period": peak_users_period["period"] if trends else None,
                        "peak_users": peak_users_period["metrics"]["unique_users"] if trends else 0,
                        "trough_period": trough_users_period["period"] if trends else None,
                        "trough_users": trough_users_period["metrics"]["unique_users"] if trends else 0
                    },
                    "distributions": {
                        "activity_levels": activity_level_distribution,
                        "trend_directions": trend_direction_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed {period_type} usage trends across {len(trends)} periods")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in usage_trends: {e}")
        return json.dumps({
            "tool": "usage_trends",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze usage trends"
        }, indent=2)
