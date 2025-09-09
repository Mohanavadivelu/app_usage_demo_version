"""
Tool: User Total Hours
Category: User Centric
Feature ID: 71

Description:
    Comprehensive analysis of total hours for a user across all applications

Parameters:
    - user (str, required): User identifier to analyze
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - platform (str, optional): Platform to filter by
    - include_breakdown (bool, optional): Include detailed breakdown by application (default: True)

Returns:
    - Comprehensive analysis of user's total usage hours with detailed analytics and insights

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-09
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Import the mcp instance from server_instance module
from server_instance import mcp
from shared.database_utils import get_database_connection
from shared.date_utils import validate_date_range, format_date_for_db

logger = logging.getLogger(__name__)


@mcp.tool()
async def user_total_hours(
    user: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    include_breakdown: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Comprehensive analysis of total hours for a user across all applications.
    
    Provides detailed insights into user's overall usage patterns, including:
    - Total usage time across all applications
    - Usage distribution and patterns
    - Session statistics and trends
    - Platform usage analysis
    - Comparative analysis and benchmarking
    - Detailed application breakdown
    
    Args:
        user: User identifier to analyze (required)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
        include_breakdown: Include detailed breakdown by application (default: True)
    
    Returns:
        Dict containing comprehensive total hours analysis with insights
    """
    try:
        # Parameter validation
        if not user or not isinstance(user, str):
            return {
                "status": "error",
                "message": "user is required and must be a non-empty string"
            }
        
        # Validate date range
        if start_date or end_date:
            date_validation = validate_date_range(start_date, end_date)
            if not date_validation["valid"]:
                return {
                    "status": "error",
                    "message": f"Date validation failed: {date_validation['message']}"
                }
        
        # Set defaults
        include_breakdown = include_breakdown if include_breakdown is not None else True
        
        # Build main query for user total hours analysis
        query = """
        SELECT 
            user,
            SUM(duration_seconds) as total_seconds,
            COUNT(DISTINCT application_name) as unique_applications,
            COUNT(DISTINCT platform) as unique_platforms,
            COUNT(*) as total_sessions,
            AVG(duration_seconds) as avg_session_seconds,
            MIN(duration_seconds) as min_session_seconds,
            MAX(duration_seconds) as max_session_seconds,
            STDDEV(duration_seconds) as stddev_session_seconds,
            MIN(log_date) as first_usage_date,
            MAX(log_date) as last_usage_date,
            COUNT(DISTINCT log_date) as active_days
        FROM app_usage
        WHERE user = ?
        """
        
        params = [user]
        
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
        
        query += " GROUP BY user"
        
        # Execute main query
        with get_database_connection() as conn:
            cursor = conn.cursor()
            start_time = datetime.now()
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if not result:
                return {
                    "status": "success",
                    "data": {
                        "tool": "user_total_hours",
                        "description": f"Total hours analysis for user '{user}'",
                        "user": user,
                        "parameters": {
                            "start_date": start_date,
                            "end_date": end_date,
                            "platform": platform,
                            "include_breakdown": include_breakdown
                        },
                        "query_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                        "user_found": False
                    },
                    "insights": {
                        "summary": f"No usage data found for user '{user}' matching the specified criteria",
                        "recommendations": [
                            "Verify the user identifier spelling",
                            "Try expanding the date range for analysis",
                            "Check if the specified platform has recorded usage data"
                        ]
                    }
                }
            
            # Process main results
            total_seconds = result[1]
            unique_applications = result[2]
            unique_platforms = result[3]
            total_sessions = result[4]
            avg_session_seconds = result[5]
            min_session_seconds = result[6]
            max_session_seconds = result[7]
            stddev_session_seconds = result[8]
            first_usage_date = result[9]
            last_usage_date = result[10]
            active_days = result[11]
            
            # Calculate derived metrics
            total_hours = round(total_seconds / 3600, 2)
            total_minutes = round(total_seconds / 60, 2)
            usage_span_days = (datetime.strptime(last_usage_date, '%Y-%m-%d') - 
                             datetime.strptime(first_usage_date, '%Y-%m-%d')).days + 1
            activity_frequency = round((active_days / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
            hours_per_day = round(total_hours / active_days, 2) if active_days > 0 else 0
            sessions_per_day = round(total_sessions / active_days, 2) if active_days > 0 else 0
            
            # Get application breakdown if requested
            application_breakdown = []
            platform_breakdown = []
            
            if include_breakdown:
                # Application breakdown
                app_breakdown_query = """
                SELECT 
                    application_name,
                    SUM(duration_seconds) as app_seconds,
                    COUNT(*) as app_sessions,
                    COUNT(DISTINCT platform) as app_platforms,
                    MAX(log_date) as app_last_usage
                FROM app_usage
                WHERE user = ?
                """
                
                app_params = [user]
                
                # Add same filters as main query
                if start_date:
                    app_breakdown_query += " AND log_date >= ?"
                    app_params.append(format_date_for_db(start_date))
                
                if end_date:
                    app_breakdown_query += " AND log_date <= ?"
                    app_params.append(format_date_for_db(end_date))
                
                if platform:
                    app_breakdown_query += " AND platform = ?"
                    app_params.append(platform)
                
                app_breakdown_query += """
                GROUP BY application_name
                ORDER BY app_seconds DESC
                LIMIT 10
                """
                
                cursor.execute(app_breakdown_query, app_params)
                app_results = cursor.fetchall()
                
                for row in app_results:
                    days_since_last_use = (datetime.now().date() - datetime.strptime(row[4], '%Y-%m-%d').date()).days
                    app_data = {
                        "application_name": row[0],
                        "hours": round(row[1] / 3600, 2),
                        "percentage": round((row[1] / total_seconds) * 100, 2),
                        "sessions": int(row[2]),
                        "platforms": int(row[3]),
                        "last_usage_date": row[4],
                        "days_since_last_use": days_since_last_use
                    }
                    application_breakdown.append(app_data)
                
                # Platform breakdown (if not filtering by platform)
                if not platform:
                    platform_breakdown_query = """
                    SELECT 
                        platform,
                        SUM(duration_seconds) as platform_seconds,
                        COUNT(*) as platform_sessions,
                        COUNT(DISTINCT application_name) as platform_apps
                    FROM app_usage
                    WHERE user = ?
                    """
                    
                    platform_params = [user]
                    
                    if start_date:
                        platform_breakdown_query += " AND log_date >= ?"
                        platform_params.append(format_date_for_db(start_date))
                    
                    if end_date:
                        platform_breakdown_query += " AND log_date <= ?"
                        platform_params.append(format_date_for_db(end_date))
                    
                    platform_breakdown_query += """
                    GROUP BY platform
                    ORDER BY platform_seconds DESC
                    """
                    
                    cursor.execute(platform_breakdown_query, platform_params)
                    platform_results = cursor.fetchall()
                    
                    for row in platform_results:
                        platform_data = {
                            "platform": row[0],
                            "hours": round(row[1] / 3600, 2),
                            "percentage": round((row[1] / total_seconds) * 100, 2),
                            "sessions": int(row[2]),
                            "applications": int(row[3])
                        }
                        platform_breakdown.append(platform_data)
            
            # Get comparative data (user ranking)
            ranking_query = """
            SELECT COUNT(*) + 1 as user_rank
            FROM (
                SELECT user, SUM(duration_seconds) as user_total
                FROM app_usage
                GROUP BY user
                HAVING SUM(duration_seconds) > ?
            )
            """
            
            cursor.execute(ranking_query, [total_seconds])
            rank_result = cursor.fetchone()
            user_rank = int(rank_result[0]) if rank_result else 1
            
            # Get total users for percentile calculation
            total_users_query = "SELECT COUNT(DISTINCT user) FROM app_usage"
            cursor.execute(total_users_query)
            total_users = cursor.fetchone()[0]
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate insights
        # User engagement classification
        if total_hours >= 100:
            engagement_level = "Power User"
        elif total_hours >= 50:
            engagement_level = "Heavy User"
        elif total_hours >= 20:
            engagement_level = "Regular User"
        elif total_hours >= 5:
            engagement_level = "Light User"
        else:
            engagement_level = "Minimal User"
        
        # Activity pattern classification
        if activity_frequency >= 80:
            activity_pattern = "Highly Consistent"
        elif activity_frequency >= 60:
            activity_pattern = "Regularly Active"
        elif activity_frequency >= 40:
            activity_pattern = "Moderately Active"
        elif activity_frequency >= 20:
            activity_pattern = "Occasionally Active"
        else:
            activity_pattern = "Sporadically Active"
        
        # Session pattern analysis
        if avg_session_seconds >= 3600:  # 1 hour
            session_pattern = "Long Sessions"
        elif avg_session_seconds >= 1800:  # 30 minutes
            session_pattern = "Medium Sessions"
        elif avg_session_seconds >= 600:  # 10 minutes
            session_pattern = "Short Sessions"
        else:
            session_pattern = "Very Short Sessions"
        
        insights = {
            "summary": f"User '{user}' has {total_hours} total hours across {unique_applications} applications over {active_days} active days",
            "key_findings": [
                f"Total usage: {total_hours} hours ({total_minutes} minutes) across {total_sessions} sessions",
                f"Activity span: {usage_span_days} days with {activity_frequency}% frequency",
                f"Daily averages: {hours_per_day} hours and {sessions_per_day} sessions per active day",
                f"Application diversity: {unique_applications} unique applications on {unique_platforms} platforms",
                f"User classification: {engagement_level} with {activity_pattern} usage pattern"
            ],
            "user_classification": {
                "engagement_level": engagement_level,
                "activity_pattern": activity_pattern,
                "session_pattern": session_pattern,
                "user_rank": user_rank,
                "percentile": round((1 - (user_rank - 1) / total_users) * 100, 1) if total_users > 0 else 0
            },
            "recommendations": []
        }
        
        # Generate recommendations based on usage patterns
        if engagement_level in ["Power User", "Heavy User"]:
            insights["recommendations"].extend([
                "User shows high engagement - consider advanced features and integrations",
                "Leverage this user for feedback and beta testing",
                "Ensure optimal performance for their primary applications"
            ])
        elif engagement_level == "Light User":
            insights["recommendations"].extend([
                "User has moderate engagement - consider onboarding improvements",
                "Identify barriers to increased usage",
                "Provide targeted training or feature highlights"
            ])
        elif engagement_level == "Minimal User":
            insights["recommendations"].extend([
                "User shows minimal engagement - implement retention strategies",
                "Investigate onboarding experience and initial barriers",
                "Consider personalized re-engagement campaigns"
            ])
        
        # Activity pattern recommendations
        if activity_pattern in ["Highly Consistent", "Regularly Active"]:
            insights["recommendations"].append("User has consistent usage patterns - maintain current experience quality")
        elif activity_pattern == "Sporadically Active":
            insights["recommendations"].append("User has sporadic usage - investigate triggers for engagement")
        
        # Session pattern recommendations
        if session_pattern == "Very Short Sessions":
            insights["recommendations"].append("User has very short sessions - optimize for quick tasks and workflows")
        elif session_pattern == "Long Sessions":
            insights["recommendations"].append("User has long sessions - ensure application stability and performance")
        
        # Application diversity recommendations
        if unique_applications == 1:
            insights["recommendations"].append("User only uses one application - introduce them to complementary tools")
        elif unique_applications > 10:
            insights["recommendations"].append("User has high application diversity - consider workflow optimization")
        
        # Build response data
        response_data = {
            "tool": "user_total_hours",
            "description": f"Comprehensive total hours analysis for user '{user}'",
            "user": user,
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "platform": platform,
                "include_breakdown": include_breakdown
            },
            "query_time_ms": round(query_time, 2),
            "user_found": True,
            "usage_summary": {
                "total_hours": total_hours,
                "total_minutes": total_minutes,
                "total_sessions": total_sessions,
                "unique_applications": unique_applications,
                "unique_platforms": unique_platforms,
                "active_days": active_days,
                "usage_span_days": usage_span_days,
                "activity_frequency": activity_frequency
            },
            "session_statistics": {
                "avg_session_minutes": round(avg_session_seconds / 60, 2),
                "min_session_minutes": round(min_session_seconds / 60, 2),
                "max_session_minutes": round(max_session_seconds / 60, 2),
                "session_variability": round(stddev_session_seconds / 60, 2) if stddev_session_seconds else 0,
                "sessions_per_day": sessions_per_day,
                "hours_per_day": hours_per_day
            },
            "timeline": {
                "first_usage_date": first_usage_date,
                "last_usage_date": last_usage_date,
                "days_since_last_use": (datetime.now().date() - datetime.strptime(last_usage_date, '%Y-%m-%d').date()).days
            },
            "user_ranking": {
                "rank": user_rank,
                "total_users": total_users,
                "percentile": round((1 - (user_rank - 1) / total_users) * 100, 1) if total_users > 0 else 0
            }
        }
        
        # Add breakdown information if requested
        if include_breakdown:
            if application_breakdown:
                response_data["application_breakdown"] = application_breakdown
            if platform_breakdown:
                response_data["platform_breakdown"] = platform_breakdown
        
        return {
            "status": "success",
            "data": response_data,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_total_hours: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze total hours for user '{user}': {str(e)}",
            "tool": "user_total_hours"
        }
