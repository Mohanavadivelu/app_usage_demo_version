"""
Tool: Multi App Users
Category: Cross Analysis
Feature ID: 45

Description:
    Users using multiple applications - analyzes user behavior patterns
    to identify users who actively use multiple applications and their usage characteristics.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - min_apps (int, optional): Minimum number of apps a user must use to be included (default: 3)
    - time_period_days (int, optional): Time period in days to analyze (default: 30)

Returns:
    - Analytics results showing multi-app users with detailed usage patterns

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import json
import logging
from typing import Optional, Dict, Any

from shared.database_utils import execute_analytics_query, validate_parameters
from server_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def multi_app_users(
    limit: Optional[int] = 100,
    min_apps: Optional[int] = 3,
    time_period_days: Optional[int] = 30
) -> str:
    """
    Identify users using multiple applications.
    
    Analyzes user behavior to find users who actively use multiple applications
    and provides insights into their usage patterns and characteristics.
    
    Args:
        limit: Maximum number of users to return (default: 100)
        min_apps: Minimum number of apps a user must use to be included (default: 3)
        time_period_days: Time period in days to analyze (default: 30)
    
    Returns:
        JSON string containing multi-app users with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_apps is not None and (min_apps < 2 or min_apps > 50):
            raise ValueError("min_apps must be between 2 and 50")
        if time_period_days is not None and (time_period_days < 1 or time_period_days > 365):
            raise ValueError("time_period_days must be between 1 and 365")
        
        # Set defaults
        limit = limit or 100
        min_apps = min_apps or 3
        time_period_days = time_period_days or 30
        
        logger.info(f"Analyzing multi-app users with limit={limit}, min_apps={min_apps}, time_period_days={time_period_days}")
        
        # Query to find multi-app users
        query = """
        WITH user_app_stats AS (
            SELECT 
                user_id,
                COUNT(DISTINCT app_name) as total_apps_used,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                MIN(timestamp) as first_usage,
                MAX(timestamp) as last_usage,
                COUNT(DISTINCT DATE(timestamp)) as active_days,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration
            FROM app_usage 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY user_id
            HAVING COUNT(DISTINCT app_name) >= ?
        ),
        user_app_details AS (
            SELECT 
                u.user_id,
                GROUP_CONCAT(DISTINCT u.app_name) as apps_used,
                COUNT(DISTINCT u.app_name) as app_count,
                SUM(u.duration_minutes) as total_duration,
                COUNT(*) as session_count
            FROM app_usage u
            WHERE u.timestamp >= datetime('now', '-' || ? || ' days')
                AND u.user_id IN (SELECT user_id FROM user_app_stats)
            GROUP BY u.user_id
        ),
        user_engagement_analysis AS (
            SELECT 
                uas.*,
                uad.apps_used,
                ROUND(uas.total_duration_minutes / uas.total_apps_used, 2) as avg_duration_per_app,
                ROUND(uas.total_sessions * 1.0 / uas.total_apps_used, 2) as avg_sessions_per_app,
                ROUND(uas.active_days * 100.0 / ?, 2) as activity_percentage,
                CASE 
                    WHEN uas.total_apps_used >= 10 THEN 'Power User'
                    WHEN uas.total_apps_used >= 7 THEN 'Heavy User'
                    WHEN uas.total_apps_used >= 5 THEN 'Moderate User'
                    ELSE 'Light Multi-User'
                END as user_category,
                CASE 
                    WHEN uas.avg_session_duration >= 60 THEN 'Long Sessions'
                    WHEN uas.avg_session_duration >= 30 THEN 'Medium Sessions'
                    WHEN uas.avg_session_duration >= 15 THEN 'Short Sessions'
                    ELSE 'Very Short Sessions'
                END as session_pattern,
                CASE 
                    WHEN uas.active_days >= ? * 0.8 THEN 'Highly Active'
                    WHEN uas.active_days >= ? * 0.5 THEN 'Moderately Active'
                    WHEN uas.active_days >= ? * 0.2 THEN 'Occasionally Active'
                    ELSE 'Rarely Active'
                END as activity_level
            FROM user_app_stats uas
            JOIN user_app_details uad ON uas.user_id = uad.user_id
        )
        SELECT 
            user_id,
            total_apps_used,
            total_sessions,
            total_duration_minutes,
            first_usage,
            last_usage,
            active_days,
            avg_session_duration,
            apps_used,
            avg_duration_per_app,
            avg_sessions_per_app,
            activity_percentage,
            user_category,
            session_pattern,
            activity_level
        FROM user_engagement_analysis
        ORDER BY total_apps_used DESC, total_duration_minutes DESC
        LIMIT ?
        """
        
        params = (time_period_days, min_apps, time_period_days, time_period_days, 
                 time_period_days, time_period_days, time_period_days, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "multi_app_users",
                "status": "success",
                "message": "No multi-app users found with the specified criteria",
                "data": {
                    "users": [],
                    "total_users": 0,
                    "parameters": {
                        "limit": limit,
                        "min_apps": min_apps,
                        "time_period_days": time_period_days
                    }
                }
            }, indent=2)
        
        # Process results
        users = []
        category_distribution = {}
        session_pattern_distribution = {}
        activity_level_distribution = {}
        
        for row in results:
            user_data = {
                "user_id": row[0],
                "app_usage_summary": {
                    "total_apps_used": row[1],
                    "total_sessions": row[2],
                    "total_duration_minutes": row[3],
                    "active_days": row[6],
                    "avg_session_duration": row[7],
                    "avg_duration_per_app": row[9],
                    "avg_sessions_per_app": row[10],
                    "activity_percentage": row[11]
                },
                "usage_period": {
                    "first_usage": row[4],
                    "last_usage": row[5]
                },
                "apps_used": row[8].split(',') if row[8] else [],
                "user_classification": {
                    "user_category": row[12],
                    "session_pattern": row[13],
                    "activity_level": row[14]
                }
            }
            users.append(user_data)
            
            # Update distributions
            category_distribution[row[12]] = category_distribution.get(row[12], 0) + 1
            session_pattern_distribution[row[13]] = session_pattern_distribution.get(row[13], 0) + 1
            activity_level_distribution[row[14]] = activity_level_distribution.get(row[14], 0) + 1
        
        # Calculate summary statistics
        if users:
            total_apps_across_users = sum(user["app_usage_summary"]["total_apps_used"] for user in users)
            avg_apps_per_user = round(total_apps_across_users / len(users), 2)
            
            total_duration_across_users = sum(user["app_usage_summary"]["total_duration_minutes"] for user in users)
            avg_duration_per_user = round(total_duration_across_users / len(users), 2)
            
            max_apps_user = max(users, key=lambda x: x["app_usage_summary"]["total_apps_used"])
            most_active_user = max(users, key=lambda x: x["app_usage_summary"]["total_duration_minutes"])
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if users:
            # Top user insights
            insights.append(f"Top multi-app user uses {max_apps_user['app_usage_summary']['total_apps_used']} different applications")
            insights.append(f"Average apps per multi-user: {avg_apps_per_user}")
            insights.append(f"Most active user spent {most_active_user['app_usage_summary']['total_duration_minutes']} minutes across apps")
            
            # Category insights
            power_users = category_distribution.get('Power User', 0)
            if power_users > 0:
                insights.append(f"Found {power_users} power users (10+ apps each)")
            
            highly_active = activity_level_distribution.get('Highly Active', 0)
            if highly_active > 0:
                insights.append(f"{highly_active} users are highly active (80%+ days in period)")
            
            # Recommendations
            if power_users > 0:
                recommendations.append("Create premium features or advanced workflows for power users")
                recommendations.append("Consider power user feedback for new feature development")
            
            if highly_active > 0:
                recommendations.append("Develop loyalty programs for highly active multi-app users")
            
            recommendations.append("Analyze app combinations used by multi-app users for integration opportunities")
            recommendations.append("Create personalized dashboards for users with diverse app usage")
            recommendations.append("Consider cross-app data synchronization features")
        
        response_data = {
            "tool": "multi_app_users",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "users": users,
                "summary": {
                    "total_users": len(users),
                    "parameters_used": {
                        "limit": limit,
                        "min_apps": min_apps,
                        "time_period_days": time_period_days
                    },
                    "statistics": {
                        "avg_apps_per_user": avg_apps_per_user if users else 0,
                        "avg_duration_per_user_minutes": avg_duration_per_user if users else 0,
                        "max_apps_by_single_user": max_apps_user["app_usage_summary"]["total_apps_used"] if users else 0
                    },
                    "distributions": {
                        "user_categories": category_distribution,
                        "session_patterns": session_pattern_distribution,
                        "activity_levels": activity_level_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed {len(users)} multi-app users")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in multi_app_users: {e}")
        return json.dumps({
            "tool": "multi_app_users",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze multi-app users"
        }, indent=2)
