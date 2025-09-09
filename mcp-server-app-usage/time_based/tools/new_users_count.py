"""
Tool: New Users Count
Category: Time Based
Feature ID: 53

Description:
    Count new users in time periods - analyzes user acquisition patterns
    across different time periods with detailed growth analysis and insights.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - period_type (str, optional): Aggregation period ('daily', 'weekly', 'monthly') (default: 'daily')
    - limit (int, optional): Maximum number of periods to return (default: 100)

Returns:
    - Count new users in time periods with detailed analytics

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
async def new_users_count(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period_type: Optional[str] = "daily",
    limit: Optional[int] = 100
) -> str:
    """
    Count new users in time periods.
    
    Analyzes user acquisition patterns across different time periods,
    providing insights into growth trends and user onboarding patterns.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        period_type: Aggregation period ('daily', 'weekly', 'monthly') (default: 'daily')
        limit: Maximum number of periods to return (default: 100)
    
    Returns:
        JSON string containing new user counts with detailed analytics
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
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing new users from {start_date} to {end_date} with period_type={period_type}, limit={limit}")
        
        # Build date grouping based on period_type
        if period_type == 'daily':
            date_group = "DATE(first_usage)"
            date_format = "DATE(first_usage)"
        elif period_type == 'weekly':
            date_group = "strftime('%Y-W%W', first_usage)"
            date_format = "strftime('%Y-W%W', first_usage)"
        else:  # monthly
            date_group = "strftime('%Y-%m', first_usage)"
            date_format = "strftime('%Y-%m', first_usage)"
        
        # Query to count new users by time period
        query = f"""
        WITH user_first_usage AS (
            SELECT 
                user_id,
                MIN(timestamp) as first_usage,
                COUNT(*) as first_day_sessions,
                SUM(duration_minutes) as first_day_duration,
                COUNT(DISTINCT app_name) as first_day_apps
            FROM app_usage
            GROUP BY user_id
        ),
        period_new_users AS (
            SELECT 
                {date_format} as period,
                COUNT(*) as new_users_count,
                SUM(first_day_sessions) as total_first_day_sessions,
                SUM(first_day_duration) as total_first_day_duration,
                ROUND(AVG(first_day_sessions), 2) as avg_first_day_sessions,
                ROUND(AVG(first_day_duration), 2) as avg_first_day_duration,
                ROUND(AVG(first_day_apps), 2) as avg_first_day_apps,
                MIN(first_usage) as period_start,
                MAX(first_usage) as period_end
            FROM user_first_usage
            WHERE DATE(first_usage) BETWEEN ? AND ?
            GROUP BY {date_group}
        ),
        cumulative_analysis AS (
            SELECT 
                *,
                SUM(new_users_count) OVER (ORDER BY period ROWS UNBOUNDED PRECEDING) as cumulative_new_users,
                LAG(new_users_count) OVER (ORDER BY period) as prev_new_users,
                CASE 
                    WHEN new_users_count >= 100 THEN 'High Acquisition'
                    WHEN new_users_count >= 50 THEN 'Moderate Acquisition'
                    WHEN new_users_count >= 20 THEN 'Low Acquisition'
                    ELSE 'Very Low Acquisition'
                END as acquisition_level
            FROM period_new_users
        ),
        growth_analysis AS (
            SELECT 
                *,
                CASE 
                    WHEN prev_new_users IS NULL THEN 0
                    WHEN prev_new_users = 0 THEN 100
                    ELSE ROUND(((new_users_count - prev_new_users) * 100.0 / prev_new_users), 2)
                END as growth_percentage,
                CASE 
                    WHEN prev_new_users IS NULL THEN 'No Previous Data'
                    WHEN new_users_count > prev_new_users THEN 'Growing'
                    WHEN new_users_count < prev_new_users THEN 'Declining'
                    ELSE 'Stable'
                END as growth_trend,
                ROUND(total_first_day_duration / new_users_count, 2) as avg_onboarding_engagement
            FROM cumulative_analysis
        )
        SELECT 
            period,
            new_users_count,
            total_first_day_sessions,
            total_first_day_duration,
            avg_first_day_sessions,
            avg_first_day_duration,
            avg_first_day_apps,
            period_start,
            period_end,
            cumulative_new_users,
            prev_new_users,
            acquisition_level,
            growth_percentage,
            growth_trend,
            avg_onboarding_engagement
        FROM growth_analysis
        ORDER BY period DESC
        LIMIT ?
        """
        
        params = (start_date, end_date, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "new_users_count",
                "status": "success",
                "message": "No new user data found for the specified period",
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
        acquisition_level_distribution = {}
        growth_trend_distribution = {}
        
        for row in results:
            period_data = {
                "period": row[0],
                "acquisition_metrics": {
                    "new_users_count": row[1],
                    "cumulative_new_users": row[9]
                },
                "onboarding_analysis": {
                    "total_first_day_sessions": row[2],
                    "total_first_day_duration": row[3],
                    "avg_first_day_sessions": row[4],
                    "avg_first_day_duration": row[5],
                    "avg_first_day_apps": row[6],
                    "avg_onboarding_engagement": row[14]
                },
                "period_info": {
                    "period_start": row[7],
                    "period_end": row[8]
                },
                "growth_analysis": {
                    "prev_new_users": row[10],
                    "growth_percentage": row[12],
                    "growth_trend": row[13]
                },
                "classification": {
                    "acquisition_level": row[11]
                }
            }
            periods.append(period_data)
            
            # Update distributions
            acquisition_level = row[11]
            growth_trend = row[13]
            acquisition_level_distribution[acquisition_level] = acquisition_level_distribution.get(acquisition_level, 0) + 1
            growth_trend_distribution[growth_trend] = growth_trend_distribution.get(growth_trend, 0) + 1
        
        # Calculate summary statistics
        if periods:
            total_periods = len(periods)
            total_new_users = sum(period["acquisition_metrics"]["new_users_count"] for period in periods)
            avg_new_users_per_period = round(total_new_users / total_periods, 2)
            
            max_acquisition_period = max(periods, key=lambda x: x["acquisition_metrics"]["new_users_count"])
            min_acquisition_period = min(periods, key=lambda x: x["acquisition_metrics"]["new_users_count"])
            
            # Calculate overall growth trend
            growing_periods = growth_trend_distribution.get('Growing', 0)
            declining_periods = growth_trend_distribution.get('Declining', 0)
            
            if growing_periods > declining_periods:
                overall_growth_trend = 'Growing'
            elif declining_periods > growing_periods:
                overall_growth_trend = 'Declining'
            else:
                overall_growth_trend = 'Mixed'
            
            # Calculate average onboarding metrics
            avg_onboarding_sessions = sum(period["onboarding_analysis"]["avg_first_day_sessions"] for period in periods) / total_periods
            avg_onboarding_duration = sum(period["onboarding_analysis"]["avg_first_day_duration"] for period in periods) / total_periods
            avg_onboarding_apps = sum(period["onboarding_analysis"]["avg_first_day_apps"] for period in periods) / total_periods
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if periods:
            insights.append(f"Analyzed {total_periods} {period_type} periods with {total_new_users} total new users")
            insights.append(f"Average {avg_new_users_per_period} new users per {period_type.rstrip('ly')} period")
            insights.append(f"Peak acquisition: {max_acquisition_period['acquisition_metrics']['new_users_count']} users in {max_acquisition_period['period']}")
            insights.append(f"Lowest acquisition: {min_acquisition_period['acquisition_metrics']['new_users_count']} users in {min_acquisition_period['period']}")
            insights.append(f"Overall growth trend: {overall_growth_trend}")
            
            # Onboarding insights
            insights.append(f"New users average {round(avg_onboarding_sessions, 1)} sessions and {round(avg_onboarding_duration, 1)} minutes on first day")
            insights.append(f"New users try {round(avg_onboarding_apps, 1)} different apps on average during onboarding")
            
            # Acquisition level insights
            high_acquisition = acquisition_level_distribution.get('High Acquisition', 0)
            if high_acquisition > 0:
                insights.append(f"{high_acquisition} periods show high user acquisition (100+ new users)")
            
            # Growth trend insights
            if growing_periods > 0:
                insights.append(f"{growing_periods} periods show acquisition growth")
            if declining_periods > 0:
                insights.append(f"{declining_periods} periods show acquisition decline")
            
            # Recommendations
            if overall_growth_trend == 'Growing':
                recommendations.append("Scale marketing efforts to capitalize on growth momentum")
                recommendations.append("Ensure onboarding infrastructure can handle increasing new users")
            elif overall_growth_trend == 'Declining':
                recommendations.append("Investigate causes of declining user acquisition")
                recommendations.append("Review and optimize marketing channels and campaigns")
            
            if avg_onboarding_sessions < 2:
                recommendations.append("Improve onboarding experience to increase first-day engagement")
                recommendations.append("Consider guided tutorials or welcome flows")
            
            if avg_onboarding_apps < 1.5:
                recommendations.append("Encourage new users to explore multiple applications")
                recommendations.append("Implement cross-app recommendations during onboarding")
            
            if high_acquisition > 0:
                recommendations.append("Analyze high-acquisition periods to identify successful strategies")
                recommendations.append("Replicate conditions that drive peak user acquisition")
            
            recommendations.append(f"Monitor {period_type} new user trends for acquisition forecasting")
            recommendations.append("Set up alerts for significant changes in acquisition patterns")
        
        response_data = {
            "tool": "new_users_count",
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
                        "total_new_users": total_new_users if periods else 0,
                        "avg_new_users_per_period": avg_new_users_per_period if periods else 0,
                        "max_acquisition_in_period": max_acquisition_period["acquisition_metrics"]["new_users_count"] if periods else 0,
                        "min_acquisition_in_period": min_acquisition_period["acquisition_metrics"]["new_users_count"] if periods else 0,
                        "overall_growth_trend": overall_growth_trend if periods else "No Data",
                        "avg_onboarding_sessions": round(avg_onboarding_sessions, 2) if periods else 0,
                        "avg_onboarding_duration": round(avg_onboarding_duration, 2) if periods else 0,
                        "avg_onboarding_apps": round(avg_onboarding_apps, 2) if periods else 0
                    },
                    "distributions": {
                        "acquisition_levels": acquisition_level_distribution,
                        "growth_trends": growth_trend_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed new users across {len(periods)} {period_type} periods")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in new_users_count: {e}")
        return json.dumps({
            "tool": "new_users_count",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze new users count"
        }, indent=2)
