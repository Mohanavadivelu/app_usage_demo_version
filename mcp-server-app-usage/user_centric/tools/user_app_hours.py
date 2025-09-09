"""
Tool: User App Hours
Category: User Centric
Feature ID: 66

Description:
    Comprehensive analysis of hours spent by a specific user on a specific application

Parameters:
    - user (str, required): User identifier to analyze
    - application_name (str, required): Application name to analyze
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - platform (str, optional): Platform to filter by

Returns:
    - Comprehensive analysis of user's application usage with detailed analytics and insights

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-09
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Import the mcp instance from server_instance module
from server_instance import mcp
from shared.database_utils import get_database_connection
from shared.date_utils import validate_date_range, format_date_for_db

logger = logging.getLogger(__name__)


@mcp.tool()
async def user_app_hours(
    user: str,
    application_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive analysis of hours spent by a specific user on a specific application.
    
    Provides detailed insights into individual user's application usage patterns, including:
    - Total usage time and session statistics
    - Daily usage patterns and trends
    - Session length analysis and variability
    - Platform usage distribution
    - Usage frequency and consistency metrics
    - Comparative analysis against other users
    
    Args:
        user: User identifier to analyze (required)
        application_name: Application name to analyze (required)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
    
    Returns:
        Dict containing comprehensive user-application usage analysis with insights
    """
    try:
        # Parameter validation
        if not user or not isinstance(user, str):
            return {
                "status": "error",
                "message": "user is required and must be a non-empty string"
            }
        
        if not application_name or not isinstance(application_name, str):
            return {
                "status": "error",
                "message": "application_name is required and must be a non-empty string"
            }
        
        # Validate date range
        if start_date or end_date:
            date_validation = validate_date_range(start_date, end_date)
            if not date_validation["valid"]:
                return {
                    "status": "error",
                    "message": f"Date validation failed: {date_validation['message']}"
                }
        
        # Build main query for user-application analysis
        query = """
        SELECT 
            user,
            application_name,
            platform,
            SUM(duration_seconds) as total_seconds,
            COUNT(*) as total_sessions,
            AVG(duration_seconds) as avg_session_seconds,
            MIN(duration_seconds) as min_session_seconds,
            MAX(duration_seconds) as max_session_seconds,
            STDDEV(duration_seconds) as stddev_session_seconds,
            MIN(log_date) as first_usage_date,
            MAX(log_date) as last_usage_date,
            COUNT(DISTINCT log_date) as active_days,
            COUNT(DISTINCT platform) as platforms_used
        FROM app_usage
        WHERE user = ? AND application_name = ?
        """
        
        params = [user, application_name]
        
        # Add date filters
        if start_date:
            query += " AND log_date >= ?"
            params.append(format_date_for_db(start_date))
        
        if end_date:
            query += " AND log_date <= ?"
            params.append(format_date_for_db(end_date))
        
        # Add platform filter
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        query += " GROUP BY user, application_name, platform"
        
        # Execute main query
        with get_database_connection() as conn:
            cursor = conn.cursor()
            start_time = datetime.now()
            cursor.execute(query, params)
            results = cursor.fetchall()
            query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if not results:
            return {
                "status": "success",
                "data": {
                    "tool": "user_app_hours",
                    "description": f"Usage analysis for user '{user}' on application '{application_name}'",
                    "user": user,
                    "application_name": application_name,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "platform": platform
                    },
                    "query_time_ms": round(query_time, 2),
                    "usage_found": False
                },
                "insights": {
                    "summary": f"No usage data found for user '{user}' on application '{application_name}' matching the specified criteria",
                    "recommendations": [
                        "Verify the user identifier and application name spelling",
                        "Try expanding the date range for analysis",
                        "Check if the specified platform has recorded usage data"
                    ]
                }
            }
        
        # Get comparative statistics
        comp_query = """
        SELECT 
            AVG(user_total_seconds) as avg_user_usage_seconds,
            STDDEV(user_total_seconds) as stddev_user_usage_seconds,
            COUNT(*) as total_app_users,
            MIN(user_total_seconds) as min_user_usage_seconds,
            MAX(user_total_seconds) as max_user_usage_seconds
        FROM (
            SELECT 
                user,
                SUM(duration_seconds) as user_total_seconds
            FROM app_usage
            WHERE application_name = ?
            GROUP BY user
        )
        """
        
        cursor.execute(comp_query, [application_name])
        comp_results = cursor.fetchone()
        
        # Process results
        total_seconds = sum(row[3] for row in results)
        total_sessions = sum(row[4] for row in results)
        platforms_data = []
        
        for row in results:
            platform_data = {
                "platform": row[2],
                "total_hours": round(row[3] / 3600, 2),
                "total_minutes": round(row[3] / 60, 2),
                "total_sessions": int(row[4]),
                "avg_session_minutes": round(row[5] / 60, 2),
                "min_session_minutes": round(row[6] / 60, 2),
                "max_session_minutes": round(row[7] / 60, 2),
                "session_variability": round(row[8] / 60, 2) if row[8] else 0,
                "percentage_of_total": round((row[3] / total_seconds) * 100, 1) if total_seconds > 0 else 0
            }
            platforms_data.append(platform_data)
        
        # Calculate additional metrics
        first_usage = min(row[9] for row in results)
        last_usage = max(row[10] for row in results)
        active_days = max(row[11] for row in results)
        platforms_used = max(row[12] for row in results)
        
        usage_span_days = (datetime.strptime(last_usage, '%Y-%m-%d') - 
                          datetime.strptime(first_usage, '%Y-%m-%d')).days + 1
        usage_frequency = round((active_days / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
        sessions_per_day = round(total_sessions / active_days, 2) if active_days > 0 else 0
        hours_per_day = round(total_seconds / 3600 / active_days, 2) if active_days > 0 else 0
        
        # Comparative analysis
        avg_user_usage = comp_results[0] if comp_results[0] else 0
        stddev_user_usage = comp_results[1] if comp_results[1] else 0
        total_app_users = comp_results[2] if comp_results[2] else 0
        min_user_usage = comp_results[3] if comp_results[3] else 0
        max_user_usage = comp_results[4] if comp_results[4] else 0
        
        # User ranking
        rank_query = """
        SELECT COUNT(*) + 1 as user_rank
        FROM (
            SELECT user, SUM(duration_seconds) as user_total
            FROM app_usage
            WHERE application_name = ?
            GROUP BY user
            HAVING SUM(duration_seconds) > ?
        )
        """
        cursor.execute(rank_query, [application_name, total_seconds])
        user_rank = cursor.fetchone()[0] if cursor.fetchone() else 1
        
        # Generate insights
        total_hours = round(total_seconds / 3600, 2)
        
        # User category classification
        if avg_user_usage > 0:
            if total_seconds > avg_user_usage + stddev_user_usage:
                user_category = "Power User"
            elif total_seconds > avg_user_usage:
                user_category = "Heavy User"
            elif total_seconds > avg_user_usage - stddev_user_usage:
                user_category = "Regular User"
            else:
                user_category = "Light User"
        else:
            user_category = "Unknown"
        
        # Engagement level
        if total_sessions >= 50:
            engagement_level = "Very High"
        elif total_sessions >= 20:
            engagement_level = "High"
        elif total_sessions >= 10:
            engagement_level = "Medium"
        elif total_sessions >= 5:
            engagement_level = "Low"
        else:
            engagement_level = "Very Low"
        
        insights = {
            "summary": f"User '{user}' has spent {total_hours} hours on '{application_name}' across {total_sessions} sessions",
            "key_findings": [
                f"Total usage: {total_hours} hours over {active_days} active days",
                f"Average session length: {round(total_seconds / total_sessions / 60, 1)} minutes",
                f"Usage frequency: {usage_frequency}% (active {active_days} out of {usage_span_days} days)",
                f"User category: {user_category}",
                f"Engagement level: {engagement_level}"
            ],
            "comparative_analysis": {
                "user_rank": user_rank,
                "total_app_users": total_app_users,
                "percentile": round((1 - (user_rank - 1) / total_app_users) * 100, 1) if total_app_users > 0 else 0,
                "vs_average_usage": round(((total_seconds - avg_user_usage) / avg_user_usage) * 100, 1) if avg_user_usage > 0 else 0,
                "usage_category": user_category
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if user_category in ["Power User", "Heavy User"]:
            insights["recommendations"].append("Leverage this user as a product advocate and feedback source")
            insights["recommendations"].append("Consider this user for beta testing new features")
        elif user_category == "Light User":
            insights["recommendations"].append("Develop engagement strategies to increase usage")
            insights["recommendations"].append("Investigate barriers to adoption")
        
        if platforms_used > 1:
            insights["recommendations"].append("Study cross-platform usage patterns for workflow optimization")
        
        if usage_frequency < 50:
            insights["recommendations"].append("Implement retention strategies to increase usage consistency")
        
        days_since_last_use = (datetime.now().date() - datetime.strptime(last_usage, '%Y-%m-%d').date()).days
        if days_since_last_use > 7:
            insights["recommendations"].append(f"User hasn't used the app in {days_since_last_use} days - consider re-engagement campaign")
        
        return {
            "status": "success",
            "data": {
                "tool": "user_app_hours",
                "description": f"Comprehensive usage analysis for user '{user}' on application '{application_name}'",
                "user": user,
                "application_name": application_name,
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "platform": platform
                },
                "query_time_ms": round(query_time, 2),
                "usage_found": True,
                "usage_summary": {
                    "total_hours": total_hours,
                    "total_minutes": round(total_seconds / 60, 2),
                    "total_sessions": total_sessions,
                    "avg_session_minutes": round(total_seconds / total_sessions / 60, 2) if total_sessions > 0 else 0,
                    "active_days": active_days,
                    "platforms_used": platforms_used,
                    "usage_frequency": usage_frequency,
                    "sessions_per_day": sessions_per_day,
                    "hours_per_day": hours_per_day
                },
                "timeline": {
                    "first_usage_date": first_usage,
                    "last_usage_date": last_usage,
                    "usage_span_days": usage_span_days,
                    "days_since_last_use": days_since_last_use
                },
                "platform_breakdown": platforms_data,
                "user_classification": {
                    "user_category": user_category,
                    "engagement_level": engagement_level,
                    "user_rank": user_rank,
                    "percentile": round((1 - (user_rank - 1) / total_app_users) * 100, 1) if total_app_users > 0 else 0
                }
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_app_hours: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze usage for user '{user}' on application '{application_name}': {str(e)}",
            "tool": "user_app_hours"
        }
