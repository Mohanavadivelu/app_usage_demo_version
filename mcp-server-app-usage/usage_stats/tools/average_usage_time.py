"""
Tool: Average Usage Time
Category: Usage Stats
Feature ID: 58

Description:
    Calculate average time spent per user per application - analyzes user engagement
    patterns by calculating average session durations and usage statistics.

Parameters:
    - application_name (str, optional): Application name to filter by
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of results (default: 100)
    - min_sessions (int, optional): Minimum sessions required to include user (default: 3)

Returns:
    - Calculate average time spent per user per application with detailed analytics

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
async def average_usage_time(
    application_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    min_sessions: Optional[int] = 3
) -> str:
    """
    Calculate average time spent per user per application.
    
    Analyzes user engagement patterns by calculating average session durations,
    total usage time, and usage consistency across users and applications.
    
    Args:
        application_name: Application name to filter by (optional)
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        limit: Maximum number of results (default: 100)
        min_sessions: Minimum sessions required to include user (default: 3)
    
    Returns:
        JSON string containing average usage time analysis with detailed insights
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_sessions is not None and (min_sessions < 1 or min_sessions > 100):
            raise ValueError("min_sessions must be between 1 and 100")
        
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
        min_sessions = min_sessions or 3
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing average usage time from {start_date} to {end_date} for {application_name or 'all applications'}")
        
        # Build application filter
        app_filter = ""
        params = [start_date, end_date, min_sessions]
        if application_name:
            app_filter = "AND app_name = ?"
            params.insert(2, application_name)
        
        # Query to calculate average usage time per user per application
        query = f"""
        WITH user_app_stats AS (
            SELECT 
                user_id,
                app_name,
                COUNT(*) as session_count,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                MIN(timestamp) as first_usage,
                MAX(timestamp) as last_usage,
                COUNT(DISTINCT DATE(timestamp)) as active_days,
                ROUND(SUM(duration_minutes) / COUNT(DISTINCT DATE(timestamp)), 2) as avg_daily_minutes
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            {app_filter}
            GROUP BY user_id, app_name
            HAVING COUNT(*) >= ?
        ),
        usage_analysis AS (
            SELECT 
                *,
                julianday(last_usage) - julianday(first_usage) + 1 as usage_span_days,
                ROUND(session_count * 1.0 / (julianday(last_usage) - julianday(first_usage) + 1), 2) as sessions_per_day,
                CASE 
                    WHEN avg_session_duration >= 60 THEN 'Long Sessions'
                    WHEN avg_session_duration >= 30 THEN 'Medium Sessions'
                    WHEN avg_session_duration >= 15 THEN 'Short Sessions'
                    ELSE 'Very Short Sessions'
                END as session_length_category,
                CASE 
                    WHEN total_duration_minutes >= 480 THEN 'Heavy User'
                    WHEN total_duration_minutes >= 240 THEN 'Moderate User'
                    WHEN total_duration_minutes >= 60 THEN 'Light User'
                    ELSE 'Minimal User'
                END as usage_intensity,
                CASE 
                    WHEN active_days >= 20 THEN 'Daily User'
                    WHEN active_days >= 10 THEN 'Regular User'
                    WHEN active_days >= 5 THEN 'Occasional User'
                    ELSE 'Rare User'
                END as usage_frequency
            FROM user_app_stats
        ),
        ranked_analysis AS (
            SELECT 
                *,
                RANK() OVER (ORDER BY avg_session_duration DESC) as duration_rank,
                RANK() OVER (ORDER BY total_duration_minutes DESC) as total_usage_rank,
                RANK() OVER (ORDER BY session_count DESC) as session_count_rank
            FROM usage_analysis
        )
        SELECT 
            user_id,
            app_name,
            session_count,
            total_duration_minutes,
            avg_session_duration,
            first_usage,
            last_usage,
            active_days,
            avg_daily_minutes,
            usage_span_days,
            sessions_per_day,
            session_length_category,
            usage_intensity,
            usage_frequency,
            duration_rank,
            total_usage_rank,
            session_count_rank
        FROM ranked_analysis
        ORDER BY avg_session_duration DESC, total_duration_minutes DESC
        LIMIT ?
        """
        
        params.append(limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "average_usage_time",
                "status": "success",
                "message": "No usage data found with the specified criteria",
                "data": {
                    "user_app_usage": [],
                    "total_records": 0,
                    "parameters": {
                        "application_name": application_name,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "min_sessions": min_sessions
                    }
                }
            }, indent=2)
        
        # Process results
        user_app_usage = []
        session_length_distribution = {}
        usage_intensity_distribution = {}
        usage_frequency_distribution = {}
        
        for row in results:
            usage_data = {
                "user_id": row[0],
                "app_name": row[1],
                "usage_metrics": {
                    "session_count": row[2],
                    "total_duration_minutes": row[3],
                    "avg_session_duration": row[4],
                    "active_days": row[7],
                    "avg_daily_minutes": row[8],
                    "usage_span_days": row[9],
                    "sessions_per_day": row[10]
                },
                "usage_period": {
                    "first_usage": row[5],
                    "last_usage": row[6]
                },
                "classification": {
                    "session_length_category": row[11],
                    "usage_intensity": row[12],
                    "usage_frequency": row[13]
                },
                "rankings": {
                    "duration_rank": row[14],
                    "total_usage_rank": row[15],
                    "session_count_rank": row[16]
                }
            }
            user_app_usage.append(usage_data)
            
            # Update distributions
            session_length = row[11]
            usage_intensity = row[12]
            usage_frequency = row[13]
            
            session_length_distribution[session_length] = session_length_distribution.get(session_length, 0) + 1
            usage_intensity_distribution[usage_intensity] = usage_intensity_distribution.get(usage_intensity, 0) + 1
            usage_frequency_distribution[usage_frequency] = usage_frequency_distribution.get(usage_frequency, 0) + 1
        
        # Calculate summary statistics
        if user_app_usage:
            total_records = len(user_app_usage)
            
            # Overall averages
            avg_session_duration_overall = sum(usage["usage_metrics"]["avg_session_duration"] for usage in user_app_usage) / total_records
            avg_total_duration = sum(usage["usage_metrics"]["total_duration_minutes"] for usage in user_app_usage) / total_records
            avg_sessions_per_user = sum(usage["usage_metrics"]["session_count"] for usage in user_app_usage) / total_records
            
            # Top performers
            longest_avg_session = max(user_app_usage, key=lambda x: x["usage_metrics"]["avg_session_duration"])
            highest_total_usage = max(user_app_usage, key=lambda x: x["usage_metrics"]["total_duration_minutes"])
            most_sessions = max(user_app_usage, key=lambda x: x["usage_metrics"]["session_count"])
            
            # Application-specific analysis if filtering by app
            if application_name:
                unique_users = len(set(usage["user_id"] for usage in user_app_usage))
                total_app_usage = sum(usage["usage_metrics"]["total_duration_minutes"] for usage in user_app_usage)
            else:
                unique_apps = len(set(usage["app_name"] for usage in user_app_usage))
                unique_users = len(set(usage["user_id"] for usage in user_app_usage))
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if user_app_usage:
            insights.append(f"Analyzed {total_records} user-app combinations")
            insights.append(f"Average session duration: {round(avg_session_duration_overall, 1)} minutes")
            insights.append(f"Average total usage per user-app: {round(avg_total_duration, 1)} minutes")
            insights.append(f"Average sessions per user-app: {round(avg_sessions_per_user, 1)}")
            
            if application_name:
                insights.append(f"Application '{application_name}' has {unique_users} active users")
                insights.append(f"Total usage for {application_name}: {round(total_app_usage, 1)} minutes")
            else:
                insights.append(f"Analysis covers {unique_users} unique users across {unique_apps} applications")
            
            insights.append(f"Longest average session: {longest_avg_session['user_id']} with {longest_avg_session['app_name']} ({longest_avg_session['usage_metrics']['avg_session_duration']} min)")
            insights.append(f"Highest total usage: {highest_total_usage['user_id']} with {highest_total_usage['app_name']} ({highest_total_usage['usage_metrics']['total_duration_minutes']} min)")
            
            # Distribution insights
            long_sessions = session_length_distribution.get('Long Sessions', 0)
            heavy_users = usage_intensity_distribution.get('Heavy User', 0)
            daily_users = usage_frequency_distribution.get('Daily User', 0)
            
            if long_sessions > 0:
                insights.append(f"{long_sessions} user-app combinations have long sessions (60+ minutes)")
            if heavy_users > 0:
                insights.append(f"{heavy_users} user-app combinations show heavy usage (8+ hours total)")
            if daily_users > 0:
                insights.append(f"{daily_users} user-app combinations represent daily usage patterns")
            
            # Recommendations
            if avg_session_duration_overall < 15:
                recommendations.append("Focus on increasing user engagement to extend session durations")
                recommendations.append("Consider implementing features that encourage longer usage sessions")
            elif avg_session_duration_overall > 45:
                recommendations.append("High engagement detected - ensure app performance can handle extended sessions")
            
            if heavy_users > 0:
                recommendations.append("Develop premium features or advanced functionality for heavy users")
                recommendations.append("Consider heavy user feedback for product development priorities")
            
            if daily_users > 0:
                recommendations.append("Leverage daily usage patterns for habit-forming features")
                recommendations.append("Consider push notifications and reminders for daily users")
            
            if long_sessions > 0:
                recommendations.append("Analyze long session patterns to identify engaging features")
                recommendations.append("Optimize app performance for extended usage periods")
            
            recommendations.append("Use average usage time data for user segmentation and personalization")
            recommendations.append("Monitor usage time trends to identify engagement changes")
            recommendations.append("Consider usage time in user retention and churn prediction models")
        
        response_data = {
            "tool": "average_usage_time",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "user_app_usage": user_app_usage,
                "summary": {
                    "total_records": len(user_app_usage),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "application_name": application_name,
                        "limit": limit,
                        "min_sessions": min_sessions
                    },
                    "statistics": {
                        "avg_session_duration_overall": round(avg_session_duration_overall, 2) if user_app_usage else 0,
                        "avg_total_duration_per_user_app": round(avg_total_duration, 2) if user_app_usage else 0,
                        "avg_sessions_per_user_app": round(avg_sessions_per_user, 2) if user_app_usage else 0,
                        "unique_users": unique_users if user_app_usage else 0,
                        "unique_apps": unique_apps if user_app_usage and not application_name else 1 if application_name else 0
                    },
                    "distributions": {
                        "session_length_categories": session_length_distribution,
                        "usage_intensity": usage_intensity_distribution,
                        "usage_frequency": usage_frequency_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed average usage time for {len(user_app_usage)} user-app combinations")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in average_usage_time: {e}")
        return json.dumps({
            "tool": "average_usage_time",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze average usage time"
        }, indent=2)
