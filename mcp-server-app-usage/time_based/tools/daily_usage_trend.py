"""
Tool: Daily Usage Trend
Category: Time Based
Feature ID: 52

Description:
    Daily usage trends for applications - analyzes daily usage patterns
    for specific applications with trend analysis and forecasting insights.

Parameters:
    - application_name (str, required): Application name to analyze
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - include_forecast (bool, optional): Include trend forecasting (default: False)

Returns:
    - Daily usage trends for applications with detailed analytics

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
async def daily_usage_trend(
    application_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_forecast: Optional[bool] = False
) -> str:
    """
    Analyze daily usage trends for applications.
    
    Provides detailed daily usage analysis for a specific application,
    including trend analysis, pattern recognition, and optional forecasting.
    
    Args:
        application_name: Application name to analyze (required)
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        include_forecast: Include trend forecasting (default: False)
    
    Returns:
        JSON string containing daily usage trends with detailed analytics
    """
    try:
        # Validate required parameters
        if not application_name or not application_name.strip():
            raise ValueError("application_name is required and cannot be empty")
        
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
        include_forecast = include_forecast or False
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing daily usage trend for {application_name} from {start_date} to {end_date}")
        
        # Query to analyze daily usage trends
        query = """
        WITH daily_usage AS (
            SELECT 
                DATE(timestamp) as usage_date,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                MIN(timestamp) as first_session,
                MAX(timestamp) as last_session
            FROM app_usage
            WHERE app_name = ? 
                AND DATE(timestamp) BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
        ),
        trend_analysis AS (
            SELECT 
                *,
                LAG(unique_users) OVER (ORDER BY usage_date) as prev_users,
                LAG(total_duration_minutes) OVER (ORDER BY usage_date) as prev_duration,
                LAG(total_sessions) OVER (ORDER BY usage_date) as prev_sessions,
                ROW_NUMBER() OVER (ORDER BY usage_date) as day_number,
                ROUND(total_duration_minutes / unique_users, 2) as avg_duration_per_user,
                ROUND(total_sessions * 1.0 / unique_users, 2) as avg_sessions_per_user
            FROM daily_usage
        ),
        growth_analysis AS (
            SELECT 
                *,
                CASE 
                    WHEN prev_users IS NULL THEN 0
                    WHEN prev_users = 0 THEN 100
                    ELSE ROUND(((unique_users - prev_users) * 100.0 / prev_users), 2)
                END as user_growth_percentage,
                CASE 
                    WHEN prev_duration IS NULL THEN 0
                    WHEN prev_duration = 0 THEN 100
                    ELSE ROUND(((total_duration_minutes - prev_duration) * 100.0 / prev_duration), 2)
                END as duration_growth_percentage,
                CASE 
                    WHEN prev_sessions IS NULL THEN 0
                    WHEN prev_sessions = 0 THEN 100
                    ELSE ROUND(((total_sessions - prev_sessions) * 100.0 / prev_sessions), 2)
                END as session_growth_percentage,
                CASE 
                    WHEN unique_users >= 100 THEN 'High Usage'
                    WHEN unique_users >= 50 THEN 'Moderate Usage'
                    WHEN unique_users >= 20 THEN 'Low Usage'
                    ELSE 'Very Low Usage'
                END as usage_level,
                CASE 
                    WHEN prev_users IS NULL THEN 'No Previous Data'
                    WHEN unique_users > prev_users THEN 'Growing'
                    WHEN unique_users < prev_users THEN 'Declining'
                    ELSE 'Stable'
                END as trend_direction
            FROM trend_analysis
        ),
        pattern_analysis AS (
            SELECT 
                *,
                CASE strftime('%w', usage_date)
                    WHEN '0' THEN 'Sunday'
                    WHEN '1' THEN 'Monday'
                    WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday'
                    WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday'
                    WHEN '6' THEN 'Saturday'
                END as day_of_week,
                CASE 
                    WHEN strftime('%w', usage_date) IN ('0', '6') THEN 'Weekend'
                    ELSE 'Weekday'
                END as day_type
            FROM growth_analysis
        )
        SELECT 
            usage_date,
            unique_users,
            total_sessions,
            total_duration_minutes,
            avg_session_duration,
            first_session,
            last_session,
            prev_users,
            prev_duration,
            prev_sessions,
            day_number,
            avg_duration_per_user,
            avg_sessions_per_user,
            user_growth_percentage,
            duration_growth_percentage,
            session_growth_percentage,
            usage_level,
            trend_direction,
            day_of_week,
            day_type
        FROM pattern_analysis
        ORDER BY usage_date
        """
        
        params = (application_name, start_date, end_date)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "daily_usage_trend",
                "status": "success",
                "message": f"No usage data found for application '{application_name}' in the specified period",
                "data": {
                    "daily_trends": [],
                    "total_days": 0,
                    "parameters": {
                        "application_name": application_name,
                        "start_date": start_date,
                        "end_date": end_date,
                        "include_forecast": include_forecast
                    }
                }
            }, indent=2)
        
        # Process results
        daily_trends = []
        usage_level_distribution = {}
        trend_direction_distribution = {}
        weekday_vs_weekend = {"Weekday": [], "Weekend": []}
        
        for row in results:
            trend_data = {
                "date": row[0],
                "metrics": {
                    "unique_users": row[1],
                    "total_sessions": row[2],
                    "total_duration_minutes": row[3],
                    "avg_session_duration": row[4],
                    "avg_duration_per_user": row[11],
                    "avg_sessions_per_user": row[12]
                },
                "session_info": {
                    "first_session": row[5],
                    "last_session": row[6]
                },
                "growth_analysis": {
                    "prev_users": row[7],
                    "prev_duration": row[8],
                    "prev_sessions": row[9],
                    "user_growth_percentage": row[13],
                    "duration_growth_percentage": row[14],
                    "session_growth_percentage": row[15]
                },
                "classification": {
                    "usage_level": row[16],
                    "trend_direction": row[17],
                    "day_of_week": row[18],
                    "day_type": row[19]
                },
                "day_number": row[10]
            }
            daily_trends.append(trend_data)
            
            # Update distributions
            usage_level = row[16]
            trend_direction = row[17]
            day_type = row[19]
            
            usage_level_distribution[usage_level] = usage_level_distribution.get(usage_level, 0) + 1
            trend_direction_distribution[trend_direction] = trend_direction_distribution.get(trend_direction, 0) + 1
            weekday_vs_weekend[day_type].append(row[1])  # unique_users
        
        # Calculate summary statistics
        if daily_trends:
            total_days = len(daily_trends)
            total_unique_users = sum(day["metrics"]["unique_users"] for day in daily_trends)
            avg_users_per_day = round(total_unique_users / total_days, 2)
            
            total_duration = sum(day["metrics"]["total_duration_minutes"] for day in daily_trends)
            avg_duration_per_day = round(total_duration / total_days, 2)
            
            max_users_day = max(daily_trends, key=lambda x: x["metrics"]["unique_users"])
            min_users_day = min(daily_trends, key=lambda x: x["metrics"]["unique_users"])
            
            # Calculate overall trend
            growing_days = trend_direction_distribution.get('Growing', 0)
            declining_days = trend_direction_distribution.get('Declining', 0)
            
            if growing_days > declining_days:
                overall_trend = 'Growing'
            elif declining_days > growing_days:
                overall_trend = 'Declining'
            else:
                overall_trend = 'Mixed'
            
            # Weekday vs Weekend analysis
            weekday_avg = round(sum(weekday_vs_weekend["Weekday"]) / len(weekday_vs_weekend["Weekday"]), 2) if weekday_vs_weekend["Weekday"] else 0
            weekend_avg = round(sum(weekday_vs_weekend["Weekend"]) / len(weekday_vs_weekend["Weekend"]), 2) if weekday_vs_weekend["Weekend"] else 0
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if daily_trends:
            insights.append(f"Analyzed {total_days} days of usage for {application_name}")
            insights.append(f"Average {avg_users_per_day} users per day with {avg_duration_per_day} minutes total usage")
            insights.append(f"Peak day: {max_users_day['date']} with {max_users_day['metrics']['unique_users']} users")
            insights.append(f"Lowest day: {min_users_day['date']} with {min_users_day['metrics']['unique_users']} users")
            insights.append(f"Overall trend: {overall_trend}")
            
            # Usage pattern insights
            if weekday_avg > 0 and weekend_avg > 0:
                if weekday_avg > weekend_avg * 1.2:
                    insights.append(f"Weekday usage significantly higher ({weekday_avg} vs {weekend_avg} users)")
                elif weekend_avg > weekday_avg * 1.2:
                    insights.append(f"Weekend usage significantly higher ({weekend_avg} vs {weekday_avg} users)")
                else:
                    insights.append(f"Balanced weekday/weekend usage ({weekday_avg} vs {weekend_avg} users)")
            
            # Usage level insights
            high_usage_days = usage_level_distribution.get('High Usage', 0)
            if high_usage_days > 0:
                insights.append(f"{high_usage_days} days show high usage (100+ users)")
            
            # Recommendations
            if overall_trend == 'Growing':
                recommendations.append("Capitalize on growth momentum with feature enhancements")
                recommendations.append("Monitor server capacity for increasing user load")
            elif overall_trend == 'Declining':
                recommendations.append("Investigate causes of declining usage")
                recommendations.append("Implement user re-engagement strategies")
            
            if weekday_avg > weekend_avg * 1.5:
                recommendations.append("Focus on business/productivity features for weekday users")
                recommendations.append("Consider weekend-specific engagement campaigns")
            elif weekend_avg > weekday_avg * 1.5:
                recommendations.append("Enhance leisure/entertainment features for weekend usage")
            
            if high_usage_days > 0:
                recommendations.append("Analyze high-usage days to identify success patterns")
                recommendations.append("Replicate conditions that drive peak usage")
            
            recommendations.append("Monitor daily trends for early detection of usage changes")
            recommendations.append("Set up alerts for significant daily usage variations")
        
        # Simple forecast if requested
        forecast_data = []
        if include_forecast and len(daily_trends) >= 7:
            # Simple linear trend forecast for next 7 days
            recent_trends = daily_trends[-7:]
            avg_growth = sum(day["growth_analysis"]["user_growth_percentage"] for day in recent_trends if day["growth_analysis"]["user_growth_percentage"] != 0) / 7
            
            last_day = daily_trends[-1]
            last_users = last_day["metrics"]["unique_users"]
            
            for i in range(1, 8):
                forecast_date = (datetime.strptime(last_day["date"], '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
                forecast_users = max(1, round(last_users * (1 + avg_growth/100) ** i))
                
                forecast_data.append({
                    "date": forecast_date,
                    "forecasted_users": forecast_users,
                    "confidence": "Low" if abs(avg_growth) > 20 else "Medium" if abs(avg_growth) > 10 else "High"
                })
        
        response_data = {
            "tool": "daily_usage_trend",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "application_name": application_name,
                "daily_trends": daily_trends,
                "summary": {
                    "total_days": len(daily_trends),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "include_forecast": include_forecast
                    },
                    "statistics": {
                        "avg_users_per_day": avg_users_per_day if daily_trends else 0,
                        "avg_duration_per_day": avg_duration_per_day if daily_trends else 0,
                        "max_users_in_day": max_users_day["metrics"]["unique_users"] if daily_trends else 0,
                        "min_users_in_day": min_users_day["metrics"]["unique_users"] if daily_trends else 0,
                        "overall_trend": overall_trend if daily_trends else "No Data",
                        "weekday_avg_users": weekday_avg if daily_trends else 0,
                        "weekend_avg_users": weekend_avg if daily_trends else 0
                    },
                    "distributions": {
                        "usage_levels": usage_level_distribution,
                        "trend_directions": trend_direction_distribution
                    }
                },
                "forecast": forecast_data if include_forecast else [],
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed daily usage trend for {application_name} across {len(daily_trends)} days")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in daily_usage_trend: {e}")
        return json.dumps({
            "tool": "daily_usage_trend",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze daily usage trend"
        }, indent=2)
