"""
Tool: Active Users Count
Category: Time Based
Feature ID: 51

Description:
    Count active users in time periods - analyzes user activity patterns
    across different time periods with detailed trend analysis and insights.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - period_type (str, optional): Aggregation period ('daily', 'weekly', 'monthly') (default: 'daily')
    - limit (int, optional): Maximum number of periods to return (default: 100)

Returns:
    - Count active users in time periods with detailed analytics

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
async def active_users_count(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period_type: Optional[str] = "daily",
    limit: Optional[int] = 100
) -> str:
    """
    Count active users in time periods.
    
    Analyzes user activity patterns across different time periods,
    providing insights into user engagement trends and patterns.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        period_type: Aggregation period ('daily', 'weekly', 'monthly') (default: 'daily')
        limit: Maximum number of periods to return (default: 100)
    
    Returns:
        JSON string containing active user counts with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        
        valid_periods = ['daily', 'weekly', 'monthly']
        if period_type and period_type not in valid_periods:
            raise ValueError(f"period_type must be one of: {', '.join(valid_periods)}")
        
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
        limit = limit or 100
        period_type = period_type or "daily"
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            # Default to 30 days before end_date
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing active users from {start_date} to {end_date} with period_type={period_type}, limit={limit}")
        
        # Build date grouping based on period_type
        if period_type == 'daily':
            date_group = "DATE(timestamp)"
            date_format = "DATE(timestamp)"
        elif period_type == 'weekly':
            date_group = "strftime('%Y-W%W', timestamp)"
            date_format = "strftime('%Y-W%W', timestamp)"
        else:  # monthly
            date_group = "strftime('%Y-%m', timestamp)"
            date_format = "strftime('%Y-%m', timestamp)"
        
        # Query to count active users by time period
        query = f"""
        WITH period_activity AS (
            SELECT 
                {date_format} as period,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(DISTINCT app_name) as active_apps,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                MIN(timestamp) as period_start,
                MAX(timestamp) as period_end
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY {date_group}
        ),
        period_analysis AS (
            SELECT 
                *,
                ROUND(total_duration_minutes / active_users, 2) as avg_duration_per_user,
                ROUND(total_sessions * 1.0 / active_users, 2) as avg_sessions_per_user,
                ROUND(active_apps * 1.0 / active_users, 2) as avg_apps_per_user,
                LAG(active_users) OVER (ORDER BY period) as prev_active_users,
                CASE 
                    WHEN active_users >= 1000 THEN 'Very High Activity'
                    WHEN active_users >= 500 THEN 'High Activity'
                    WHEN active_users >= 100 THEN 'Moderate Activity'
                    WHEN active_users >= 50 THEN 'Low Activity'
                    ELSE 'Very Low Activity'
                END as activity_level
            FROM period_activity
        ),
        trend_analysis AS (
            SELECT 
                *,
                CASE 
                    WHEN prev_active_users IS NULL THEN 0
                    WHEN prev_active_users = 0 THEN 100
                    ELSE ROUND(((active_users - prev_active_users) * 100.0 / prev_active_users), 2)
                END as growth_percentage,
                CASE 
                    WHEN prev_active_users IS NULL THEN 'No Previous Data'
                    WHEN active_users > prev_active_users THEN 'Growing'
                    WHEN active_users < prev_active_users THEN 'Declining'
                    ELSE 'Stable'
                END as trend_direction
            FROM period_analysis
        )
        SELECT 
            period,
            active_users,
            active_apps,
            total_sessions,
            total_duration_minutes,
            avg_session_duration,
            period_start,
            period_end,
            avg_duration_per_user,
            avg_sessions_per_user,
            avg_apps_per_user,
            prev_active_users,
            activity_level,
            growth_percentage,
            trend_direction
        FROM trend_analysis
        ORDER BY period DESC
        LIMIT ?
        """
        
        params = (start_date, end_date, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "active_users_count",
                "status": "success",
                "message": "No active user data found for the specified period",
                "data": {
                    "periods": [],
                    "total_periods": 0,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "period_type": period_type,
                        "limit": limit
                    }
                }
            }, indent=2)
        
        # Process results
        periods = []
        activity_level_distribution = {}
        trend_direction_distribution = {}
        
        for row in results:
            period_data = {
                "period": row[0],
                "metrics": {
                    "active_users": row[1],
                    "active_apps": row[2],
                    "total_sessions": row[3],
                    "total_duration_minutes": row[4],
                    "avg_session_duration": row[5]
                },
                "period_info": {
                    "period_start": row[6],
                    "period_end": row[7]
                },
                "user_analytics": {
                    "avg_duration_per_user": row[8],
                    "avg_sessions_per_user": row[9],
                    "avg_apps_per_user": row[10]
                },
                "trend_analysis": {
                    "prev_active_users": row[11],
                    "growth_percentage": row[13],
                    "trend_direction": row[14]
                },
                "classification": {
                    "activity_level": row[12]
                }
            }
            periods.append(period_data)
            
            # Update distributions
            activity_level = row[12]
            trend_direction = row[14]
            activity_level_distribution[activity_level] = activity_level_distribution.get(activity_level, 0) + 1
            trend_direction_distribution[trend_direction] = trend_direction_distribution.get(trend_direction, 0) + 1
        
        # Calculate summary statistics
        if periods:
            total_periods = len(periods)
            total_active_users = sum(period["metrics"]["active_users"] for period in periods)
            avg_active_users = round(total_active_users / total_periods, 2)
            
            max_users_period = max(periods, key=lambda x: x["metrics"]["active_users"])
            min_users_period = min(periods, key=lambda x: x["metrics"]["active_users"])
            
            # Calculate overall trend
            growing_periods = trend_direction_distribution.get('Growing', 0)
            declining_periods = trend_direction_distribution.get('Declining', 0)
            
            if growing_periods > declining_periods:
                overall_trend = 'Growing'
            elif declining_periods > growing_periods:
                overall_trend = 'Declining'
            else:
                overall_trend = 'Mixed'
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if periods:
            insights.append(f"Analyzed {total_periods} {period_type} periods with average {avg_active_users} active users per period")
            insights.append(f"Peak activity: {max_users_period['metrics']['active_users']} users in {max_users_period['period']}")
            insights.append(f"Lowest activity: {min_users_period['metrics']['active_users']} users in {min_users_period['period']}")
            insights.append(f"Overall trend: {overall_trend}")
            
            # Activity level insights
            high_activity = activity_level_distribution.get('High Activity', 0) + activity_level_distribution.get('Very High Activity', 0)
            if high_activity > 0:
                insights.append(f"{high_activity} periods show high user activity (500+ users)")
            
            # Trend insights
            if growing_periods > 0:
                insights.append(f"{growing_periods} periods show user growth")
            if declining_periods > 0:
                insights.append(f"{declining_periods} periods show user decline")
            
            # Recommendations
            if overall_trend == 'Growing':
                recommendations.append("Capitalize on growth momentum with user acquisition campaigns")
                recommendations.append("Ensure infrastructure can handle increasing user load")
            elif overall_trend == 'Declining':
                recommendations.append("Investigate causes of user decline and implement retention strategies")
                recommendations.append("Focus on re-engagement campaigns for inactive users")
            
            if high_activity > 0:
                recommendations.append("Analyze high-activity periods to identify success factors")
                recommendations.append("Replicate conditions that drive high user engagement")
            
            recommendations.append(f"Monitor {period_type} active user trends for early warning signs")
            recommendations.append("Set up alerts for significant changes in user activity patterns")
        
        response_data = {
            "tool": "active_users_count",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "periods": periods,
                "summary": {
                    "total_periods": len(periods),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "period_type": period_type
                    },
                    "parameters_used": {
                        "limit": limit
                    },
                    "statistics": {
                        "avg_active_users_per_period": avg_active_users if periods else 0,
                        "max_users_in_period": max_users_period["metrics"]["active_users"] if periods else 0,
                        "min_users_in_period": min_users_period["metrics"]["active_users"] if periods else 0,
                        "overall_trend": overall_trend if periods else "No Data"
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
        
        logger.info(f"Successfully analyzed active users across {len(periods)} {period_type} periods")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in active_users_count: {e}")
        return json.dumps({
            "tool": "active_users_count",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze active users count"
        }, indent=2)
