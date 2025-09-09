"""
Tool: User Last Active
Category: User Centric
Feature ID: 68

Description:
    Comprehensive analysis of when a user was last active with activity patterns

Parameters:
    - user (str, required): User identifier to analyze
    - include_details (bool, optional): Include detailed activity breakdown (default: True)

Returns:
    - Comprehensive analysis of user's last activity with detailed analytics and insights

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

logger = logging.getLogger(__name__)


@mcp.tool()
async def user_last_active(
    user: str,
    include_details: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Comprehensive analysis of when a user was last active with activity patterns.
    
    Provides detailed insights into user's recent activity and engagement patterns, including:
    - Last activity date and time analysis
    - Activity frequency and consistency metrics
    - Recent usage patterns and trends
    - Application usage in recent sessions
    - User engagement status and recommendations
    
    Args:
        user: User identifier to analyze (required)
        include_details: Include detailed activity breakdown (default: True)
    
    Returns:
        Dict containing comprehensive user activity analysis with insights
    """
    try:
        # Parameter validation
        if not user or not isinstance(user, str):
            return {
                "status": "error",
                "message": "user is required and must be a non-empty string"
            }
        
        # Set defaults
        include_details = include_details if include_details is not None else True
        
        # Build main query for user activity analysis
        query = """
        SELECT 
            user,
            MAX(log_date) as last_active_date,
            MIN(log_date) as first_active_date,
            COUNT(DISTINCT log_date) as total_active_days,
            SUM(duration_seconds) as total_seconds,
            COUNT(*) as total_sessions,
            COUNT(DISTINCT application_name) as unique_applications,
            COUNT(DISTINCT platform) as unique_platforms,
            AVG(duration_seconds) as avg_session_seconds
        FROM app_usage
        WHERE user = ?
        GROUP BY user
        """
        
        # Execute main query
        with get_database_connection() as conn:
            cursor = conn.cursor()
            start_time = datetime.now()
            cursor.execute(query, [user])
            result = cursor.fetchone()
            
            if not result:
                return {
                    "status": "success",
                    "data": {
                        "tool": "user_last_active",
                        "description": f"Last activity analysis for user '{user}'",
                        "user": user,
                        "query_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                        "user_found": False
                    },
                    "insights": {
                        "summary": f"No activity data found for user '{user}'",
                        "recommendations": [
                            "Verify the user identifier spelling",
                            "Check if the user has any recorded activity in the system",
                            "Consider if this is a new user who hasn't started using applications yet"
                        ]
                    }
                }
            
            # Process main results
            last_active_date = result[1]
            first_active_date = result[2]
            total_active_days = result[3]
            total_seconds = result[4]
            total_sessions = result[5]
            unique_applications = result[6]
            unique_platforms = result[7]
            avg_session_seconds = result[8]
            
            # Calculate derived metrics
            days_since_last_active = (datetime.now().date() - datetime.strptime(last_active_date, '%Y-%m-%d').date()).days
            total_span_days = (datetime.strptime(last_active_date, '%Y-%m-%d') - 
                             datetime.strptime(first_active_date, '%Y-%m-%d')).days + 1
            activity_frequency = round((total_active_days / total_span_days) * 100, 1) if total_span_days > 0 else 0
            
            # Determine activity status
            if days_since_last_active == 0:
                activity_status = "Active Today"
            elif days_since_last_active <= 1:
                activity_status = "Active Yesterday"
            elif days_since_last_active <= 7:
                activity_status = "Active This Week"
            elif days_since_last_active <= 30:
                activity_status = "Active This Month"
            elif days_since_last_active <= 90:
                activity_status = "Recently Inactive"
            else:
                activity_status = "Long-term Inactive"
            
            # Get recent activity details if requested
            recent_activity = []
            last_app_used = None
            last_platform_used = None
            
            if include_details:
                # Get last 10 sessions
                recent_query = """
                SELECT 
                    log_date,
                    application_name,
                    platform,
                    duration_seconds
                FROM app_usage
                WHERE user = ?
                ORDER BY log_date DESC, duration_seconds DESC
                LIMIT 10
                """
                
                cursor.execute(recent_query, [user])
                recent_results = cursor.fetchall()
                
                if recent_results:
                    last_app_used = recent_results[0][1]
                    last_platform_used = recent_results[0][2]
                    
                    for row in recent_results:
                        session_data = {
                            "date": row[0],
                            "application_name": row[1],
                            "platform": row[2],
                            "duration_minutes": round(row[3] / 60, 2),
                            "days_ago": (datetime.now().date() - datetime.strptime(row[0], '%Y-%m-%d').date()).days
                        }
                        recent_activity.append(session_data)
                
                # Get activity pattern for last 30 days
                pattern_query = """
                SELECT 
                    log_date,
                    COUNT(*) as daily_sessions,
                    SUM(duration_seconds) as daily_seconds,
                    COUNT(DISTINCT application_name) as daily_apps
                FROM app_usage
                WHERE user = ? AND log_date >= date('now', '-30 days')
                GROUP BY log_date
                ORDER BY log_date DESC
                """
                
                cursor.execute(pattern_query, [user])
                pattern_results = cursor.fetchall()
                
                activity_pattern = []
                for row in pattern_results:
                    pattern_data = {
                        "date": row[0],
                        "sessions": int(row[1]),
                        "hours": round(row[2] / 3600, 2),
                        "applications": int(row[3]),
                        "days_ago": (datetime.now().date() - datetime.strptime(row[0], '%Y-%m-%d').date()).days
                    }
                    activity_pattern.append(pattern_data)
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate insights
        total_hours = round(total_seconds / 3600, 2)
        
        # Activity classification
        if activity_frequency > 80:
            engagement_level = "Highly Engaged"
        elif activity_frequency > 60:
            engagement_level = "Regularly Engaged"
        elif activity_frequency > 40:
            engagement_level = "Moderately Engaged"
        elif activity_frequency > 20:
            engagement_level = "Occasionally Engaged"
        else:
            engagement_level = "Rarely Engaged"
        
        # Risk assessment
        if days_since_last_active <= 7:
            churn_risk = "Low"
        elif days_since_last_active <= 30:
            churn_risk = "Medium"
        elif days_since_last_active <= 90:
            churn_risk = "High"
        else:
            churn_risk = "Critical"
        
        insights = {
            "summary": f"User '{user}' was last active {days_since_last_active} days ago on {last_active_date}",
            "key_findings": [
                f"Activity status: {activity_status}",
                f"Total activity span: {total_span_days} days with {activity_frequency}% frequency",
                f"Overall usage: {total_hours} hours across {total_sessions} sessions",
                f"Application diversity: {unique_applications} unique applications on {unique_platforms} platforms",
                f"Engagement level: {engagement_level}"
            ],
            "activity_assessment": {
                "activity_status": activity_status,
                "days_since_last_active": days_since_last_active,
                "engagement_level": engagement_level,
                "churn_risk": churn_risk,
                "activity_frequency": activity_frequency
            },
            "recommendations": []
        }
        
        # Generate recommendations based on activity status
        if activity_status == "Active Today":
            insights["recommendations"].extend([
                "User is currently active - great engagement!",
                "Consider providing new features or content to maintain interest"
            ])
        elif activity_status in ["Active Yesterday", "Active This Week"]:
            insights["recommendations"].extend([
                "User is recently active - maintain engagement with regular updates",
                "Monitor for any changes in usage patterns"
            ])
        elif activity_status == "Active This Month":
            insights["recommendations"].extend([
                "User shows moderate engagement - consider re-engagement strategies",
                "Send personalized content or feature updates"
            ])
        elif activity_status == "Recently Inactive":
            insights["recommendations"].extend([
                "User is becoming inactive - implement retention strategies",
                "Send targeted re-engagement campaigns",
                "Investigate potential barriers to usage"
            ])
        else:  # Long-term Inactive
            insights["recommendations"].extend([
                "User is at high churn risk - urgent re-engagement needed",
                "Consider win-back campaigns or surveys to understand issues",
                "Evaluate if user should be moved to inactive segment"
            ])
        
        # Additional recommendations based on usage patterns
        if unique_applications == 1:
            insights["recommendations"].append("User only uses one application - introduce them to other relevant tools")
        elif unique_applications > 5:
            insights["recommendations"].append("User has diverse application usage - consider workflow optimization")
        
        if unique_platforms > 1:
            insights["recommendations"].append("User is cross-platform - ensure seamless experience across devices")
        
        # Build response data
        response_data = {
            "tool": "user_last_active",
            "description": f"Comprehensive last activity analysis for user '{user}'",
            "user": user,
            "parameters": {
                "include_details": include_details
            },
            "query_time_ms": round(query_time, 2),
            "user_found": True,
            "activity_summary": {
                "last_active_date": last_active_date,
                "days_since_last_active": days_since_last_active,
                "activity_status": activity_status,
                "last_app_used": last_app_used,
                "last_platform_used": last_platform_used
            },
            "usage_statistics": {
                "first_active_date": first_active_date,
                "total_active_days": total_active_days,
                "total_span_days": total_span_days,
                "activity_frequency": activity_frequency,
                "total_hours": total_hours,
                "total_sessions": total_sessions,
                "avg_session_minutes": round(avg_session_seconds / 60, 2),
                "unique_applications": unique_applications,
                "unique_platforms": unique_platforms
            },
            "engagement_metrics": {
                "engagement_level": engagement_level,
                "churn_risk": churn_risk,
                "sessions_per_active_day": round(total_sessions / total_active_days, 2) if total_active_days > 0 else 0,
                "hours_per_active_day": round(total_hours / total_active_days, 2) if total_active_days > 0 else 0
            }
        }
        
        # Add detailed information if requested
        if include_details:
            response_data["recent_activity"] = recent_activity
            if 'activity_pattern' in locals():
                response_data["activity_pattern_last_30_days"] = activity_pattern
        
        return {
            "status": "success",
            "data": response_data,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_last_active: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze last activity for user '{user}': {str(e)}",
            "tool": "user_last_active"
        }
