"""
Tool: Peak Usage Hours
Category: Time Based
Feature ID: 55

Description:
    Identify peak usage hours - analyzes hourly usage patterns to identify
    when applications experience the highest activity and user engagement.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - application_name (str, optional): Specific application to analyze (optional)
    - timezone (str, optional): Timezone for hour analysis (default: 'UTC')

Returns:
    - Identify peak usage hours with detailed analytics

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
async def peak_usage_hours(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    application_name: Optional[str] = None,
    timezone: Optional[str] = "UTC"
) -> str:
    """
    Identify peak usage hours across applications.
    
    Analyzes hourly usage patterns to identify when applications
    experience the highest activity and user engagement.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        application_name: Specific application to analyze (optional)
        timezone: Timezone for hour analysis (default: 'UTC')
    
    Returns:
        JSON string containing peak usage hours with detailed analytics
    """
    try:
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
        timezone = timezone or "UTC"
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing peak usage hours from {start_date} to {end_date} for {application_name or 'all applications'}")
        
        # Build application filter
        app_filter = ""
        params = [start_date, end_date]
        if application_name:
            app_filter = "AND app_name = ?"
            params.append(application_name)
        
        # Query to analyze hourly usage patterns
        query = f"""
        WITH hourly_usage AS (
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as total_sessions,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT app_name) as unique_apps,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            {app_filter}
            GROUP BY CAST(strftime('%H', timestamp) AS INTEGER)
        ),
        hourly_analysis AS (
            SELECT 
                *,
                ROUND(total_duration_minutes / total_sessions, 2) as avg_duration_per_session,
                ROUND(unique_users * 1.0 / active_days, 2) as avg_users_per_day,
                ROUND(total_sessions * 1.0 / active_days, 2) as avg_sessions_per_day,
                CASE 
                    WHEN hour BETWEEN 6 AND 11 THEN 'Morning'
                    WHEN hour BETWEEN 12 AND 17 THEN 'Afternoon'
                    WHEN hour BETWEEN 18 AND 21 THEN 'Evening'
                    ELSE 'Night'
                END as time_period,
                CASE 
                    WHEN hour BETWEEN 9 AND 17 THEN 'Business Hours'
                    ELSE 'Off Hours'
                END as business_classification
            FROM hourly_usage
        ),
        ranked_hours AS (
            SELECT 
                *,
                RANK() OVER (ORDER BY total_sessions DESC) as session_rank,
                RANK() OVER (ORDER BY unique_users DESC) as user_rank,
                RANK() OVER (ORDER BY total_duration_minutes DESC) as duration_rank,
                CASE 
                    WHEN total_sessions >= (SELECT MAX(total_sessions) * 0.8 FROM hourly_analysis) THEN 'Peak'
                    WHEN total_sessions >= (SELECT MAX(total_sessions) * 0.6 FROM hourly_analysis) THEN 'High'
                    WHEN total_sessions >= (SELECT MAX(total_sessions) * 0.4 FROM hourly_analysis) THEN 'Moderate'
                    WHEN total_sessions >= (SELECT MAX(total_sessions) * 0.2 FROM hourly_analysis) THEN 'Low'
                    ELSE 'Very Low'
                END as activity_level
            FROM hourly_analysis
        )
        SELECT 
            hour,
            total_sessions,
            unique_users,
            unique_apps,
            total_duration_minutes,
            avg_session_duration,
            active_days,
            avg_duration_per_session,
            avg_users_per_day,
            avg_sessions_per_day,
            time_period,
            business_classification,
            session_rank,
            user_rank,
            duration_rank,
            activity_level
        FROM ranked_hours
        ORDER BY hour
        """
        
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "peak_usage_hours",
                "status": "success",
                "message": "No usage data found for the specified period",
                "data": {
                    "hourly_patterns": [],
                    "total_hours_analyzed": 0,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "application_name": application_name,
                        "timezone": timezone
                    }
                }
            }, indent=2)
        
        # Process results
        hourly_patterns = []
        time_period_distribution = {}
        activity_level_distribution = {}
        business_vs_off_hours = {"Business Hours": [], "Off Hours": []}
        
        for row in results:
            hour_data = {
                "hour": row[0],
                "hour_display": f"{row[0]:02d}:00",
                "usage_metrics": {
                    "total_sessions": row[1],
                    "unique_users": row[2],
                    "unique_apps": row[3],
                    "total_duration_minutes": row[4],
                    "avg_session_duration": row[5],
                    "active_days": row[6]
                },
                "calculated_metrics": {
                    "avg_duration_per_session": row[7],
                    "avg_users_per_day": row[8],
                    "avg_sessions_per_day": row[9]
                },
                "classification": {
                    "time_period": row[10],
                    "business_classification": row[11],
                    "activity_level": row[15]
                },
                "rankings": {
                    "session_rank": row[12],
                    "user_rank": row[13],
                    "duration_rank": row[14]
                }
            }
            hourly_patterns.append(hour_data)
            
            # Update distributions
            time_period = row[10]
            activity_level = row[15]
            business_class = row[11]
            
            time_period_distribution[time_period] = time_period_distribution.get(time_period, 0) + 1
            activity_level_distribution[activity_level] = activity_level_distribution.get(activity_level, 0) + 1
            business_vs_off_hours[business_class].append(row[1])  # total_sessions
        
        # Calculate summary statistics
        if hourly_patterns:
            total_sessions_all_hours = sum(hour["usage_metrics"]["total_sessions"] for hour in hourly_patterns)
            total_users_all_hours = sum(hour["usage_metrics"]["unique_users"] for hour in hourly_patterns)
            
            # Find peak hours
            peak_session_hour = max(hourly_patterns, key=lambda x: x["usage_metrics"]["total_sessions"])
            peak_user_hour = max(hourly_patterns, key=lambda x: x["usage_metrics"]["unique_users"])
            peak_duration_hour = max(hourly_patterns, key=lambda x: x["usage_metrics"]["total_duration_minutes"])
            
            # Find lowest activity hour
            lowest_activity_hour = min(hourly_patterns, key=lambda x: x["usage_metrics"]["total_sessions"])
            
            # Business hours vs off hours analysis
            business_hours_sessions = sum(business_vs_off_hours["Business Hours"])
            off_hours_sessions = sum(business_vs_off_hours["Off Hours"])
            business_hours_avg = round(business_hours_sessions / len(business_vs_off_hours["Business Hours"]), 2) if business_vs_off_hours["Business Hours"] else 0
            off_hours_avg = round(off_hours_sessions / len(business_vs_off_hours["Off Hours"]), 2) if business_vs_off_hours["Off Hours"] else 0
            
            # Time period analysis
            morning_hours = [h for h in hourly_patterns if h["classification"]["time_period"] == "Morning"]
            afternoon_hours = [h for h in hourly_patterns if h["classification"]["time_period"] == "Afternoon"]
            evening_hours = [h for h in hourly_patterns if h["classification"]["time_period"] == "Evening"]
            night_hours = [h for h in hourly_patterns if h["classification"]["time_period"] == "Night"]
            
            morning_avg = sum(h["usage_metrics"]["total_sessions"] for h in morning_hours) / len(morning_hours) if morning_hours else 0
            afternoon_avg = sum(h["usage_metrics"]["total_sessions"] for h in afternoon_hours) / len(afternoon_hours) if afternoon_hours else 0
            evening_avg = sum(h["usage_metrics"]["total_sessions"] for h in evening_hours) / len(evening_hours) if evening_hours else 0
            night_avg = sum(h["usage_metrics"]["total_sessions"] for h in night_hours) / len(night_hours) if night_hours else 0
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if hourly_patterns:
            insights.append(f"Analyzed {len(hourly_patterns)} hours with {total_sessions_all_hours} total sessions")
            insights.append(f"Peak session hour: {peak_session_hour['hour_display']} with {peak_session_hour['usage_metrics']['total_sessions']} sessions")
            insights.append(f"Peak user hour: {peak_user_hour['hour_display']} with {peak_user_hour['usage_metrics']['unique_users']} unique users")
            insights.append(f"Lowest activity: {lowest_activity_hour['hour_display']} with {lowest_activity_hour['usage_metrics']['total_sessions']} sessions")
            
            # Business hours analysis
            if business_hours_avg > off_hours_avg * 1.5:
                insights.append(f"Business hours show significantly higher activity ({business_hours_avg:.1f} vs {off_hours_avg:.1f} avg sessions)")
            elif off_hours_avg > business_hours_avg * 1.5:
                insights.append(f"Off-hours show surprisingly high activity ({off_hours_avg:.1f} vs {business_hours_avg:.1f} avg sessions)")
            else:
                insights.append(f"Balanced usage between business hours and off-hours")
            
            # Time period insights
            time_periods = [
                ("Morning", morning_avg),
                ("Afternoon", afternoon_avg),
                ("Evening", evening_avg),
                ("Night", night_avg)
            ]
            peak_time_period = max(time_periods, key=lambda x: x[1])
            insights.append(f"Peak time period: {peak_time_period[0]} with {peak_time_period[1]:.1f} average sessions per hour")
            
            # Activity level insights
            peak_hours = activity_level_distribution.get('Peak', 0)
            high_hours = activity_level_distribution.get('High', 0)
            if peak_hours > 0:
                insights.append(f"{peak_hours} hours classified as peak activity")
            if high_hours > 0:
                insights.append(f"{high_hours} hours show high activity levels")
            
            # Recommendations
            if peak_hours > 0:
                recommendations.append("Schedule maintenance and updates during low-activity hours")
                recommendations.append("Ensure adequate server capacity during peak hours")
            
            if business_hours_avg > off_hours_avg * 2:
                recommendations.append("Consider business-focused features and support during peak business hours")
                recommendations.append("Optimize performance for professional use cases")
            elif off_hours_avg > business_hours_avg:
                recommendations.append("Focus on consumer/leisure features for off-hours usage")
                recommendations.append("Consider global user base with different time zones")
            
            if peak_time_period[0] == "Evening":
                recommendations.append("Optimize for leisure and personal use during evening hours")
            elif peak_time_period[0] == "Morning":
                recommendations.append("Focus on productivity features for morning usage patterns")
            
            recommendations.append("Use peak hour data for targeted marketing and communication timing")
            recommendations.append("Consider time-based pricing or feature availability")
            recommendations.append("Monitor hourly patterns for capacity planning and resource allocation")
        
        response_data = {
            "tool": "peak_usage_hours",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "hourly_patterns": hourly_patterns,
                "summary": {
                    "total_hours_analyzed": len(hourly_patterns),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "application_name": application_name,
                        "timezone": timezone
                    },
                    "peak_hours": {
                        "peak_session_hour": f"{peak_session_hour['hour']:02d}:00" if hourly_patterns else None,
                        "peak_user_hour": f"{peak_user_hour['hour']:02d}:00" if hourly_patterns else None,
                        "peak_duration_hour": f"{peak_duration_hour['hour']:02d}:00" if hourly_patterns else None,
                        "lowest_activity_hour": f"{lowest_activity_hour['hour']:02d}:00" if hourly_patterns else None
                    },
                    "statistics": {
                        "total_sessions_all_hours": total_sessions_all_hours if hourly_patterns else 0,
                        "business_hours_avg_sessions": business_hours_avg if hourly_patterns else 0,
                        "off_hours_avg_sessions": off_hours_avg if hourly_patterns else 0,
                        "time_period_averages": {
                            "morning": round(morning_avg, 2) if hourly_patterns else 0,
                            "afternoon": round(afternoon_avg, 2) if hourly_patterns else 0,
                            "evening": round(evening_avg, 2) if hourly_patterns else 0,
                            "night": round(night_avg, 2) if hourly_patterns else 0
                        }
                    },
                    "distributions": {
                        "time_periods": time_period_distribution,
                        "activity_levels": activity_level_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed peak usage hours across {len(hourly_patterns)} hours")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in peak_usage_hours: {e}")
        return json.dumps({
            "tool": "peak_usage_hours",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze peak usage hours"
        }, indent=2)
