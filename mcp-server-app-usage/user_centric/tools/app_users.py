"""
Tool: App Users
Category: User Centric
Feature ID: 65

Description:
    Comprehensive analysis of users who have used a specific application

Parameters:
    - application_name (str, required): Application name to analyze
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of users to return (default: 100, max: 1000)
    - platform (str, optional): Platform to filter by

Returns:
    - Comprehensive analysis of users with detailed analytics and insights

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
async def app_users(
    application_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive analysis of users who have used a specific application.
    
    Provides detailed insights into user behavior and engagement patterns, including:
    - User usage statistics and rankings
    - Session patterns and frequency
    - Platform usage distribution
    - User engagement classification
    - Temporal usage patterns and trends
    
    Args:
        application_name: Application name to analyze (required)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        limit: Maximum number of users to return (1-1000, default: 100)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
    
    Returns:
        Dict containing comprehensive user analysis with analytics and insights
    """
    try:
        # Parameter validation
        if not application_name or not isinstance(application_name, str):
            return {
                "status": "error",
                "message": "application_name is required and must be a non-empty string"
            }
        
        if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > 1000):
            return {
                "status": "error",
                "message": "limit must be an integer between 1 and 1000"
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
        limit = limit or 100
        
        # Build query with CTEs for comprehensive analysis
        query = """
        WITH user_app_stats AS (
            SELECT 
                user,
                platform,
                SUM(duration_seconds) as total_seconds,
                COUNT(*) as session_count,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds,
                STDDEV(duration_seconds) as stddev_session_seconds,
                MIN(log_date) as first_usage_date,
                MAX(log_date) as last_usage_date,
                COUNT(DISTINCT log_date) as active_days,
                COUNT(DISTINCT platform) as platforms_used
            FROM app_usage
            WHERE application_name = ?
        """
        
        params = [application_name]
        
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
        
        query += """
            GROUP BY user, platform
        ),
        aggregated_user_stats AS (
            SELECT 
                user,
                SUM(total_seconds) as total_seconds,
                SUM(session_count) as session_count,
                AVG(avg_session_seconds) as avg_session_seconds,
                MIN(min_session_seconds) as min_session_seconds,
                MAX(max_session_seconds) as max_session_seconds,
                AVG(stddev_session_seconds) as avg_stddev_session_seconds,
                MIN(first_usage_date) as first_usage_date,
                MAX(last_usage_date) as last_usage_date,
                SUM(active_days) as total_active_days,
                MAX(platforms_used) as platforms_used
            FROM user_app_stats
            GROUP BY user
        ),
        total_stats AS (
            SELECT 
                SUM(total_seconds) as grand_total_seconds,
                SUM(session_count) as grand_total_sessions,
                COUNT(*) as total_users,
                AVG(total_seconds) as avg_user_usage_seconds,
                STDDEV(total_seconds) as stddev_user_usage_seconds,
                AVG(session_count) as avg_sessions_per_user,
                STDDEV(session_count) as stddev_sessions_per_user
            FROM aggregated_user_stats
        ),
        user_analysis AS (
            SELECT 
                aus.*,
                ts.grand_total_seconds,
                ts.grand_total_sessions,
                ts.total_users,
                ts.avg_user_usage_seconds,
                ts.stddev_user_usage_seconds,
                ts.avg_sessions_per_user,
                ts.stddev_sessions_per_user,
                ROUND((aus.total_seconds * 100.0 / ts.grand_total_seconds), 2) as usage_percentage,
                ROUND((aus.session_count * 100.0 / ts.grand_total_sessions), 2) as session_percentage,
                ROW_NUMBER() OVER (ORDER BY aus.total_seconds DESC) as usage_rank,
                ROW_NUMBER() OVER (ORDER BY aus.session_count DESC) as session_rank,
                NTILE(4) OVER (ORDER BY aus.total_seconds) as usage_quartile,
                CASE 
                    WHEN aus.total_seconds > ts.avg_user_usage_seconds + ts.stddev_user_usage_seconds THEN 'Power User'
                    WHEN aus.total_seconds > ts.avg_user_usage_seconds THEN 'Heavy User'
                    WHEN aus.total_seconds > ts.avg_user_usage_seconds - ts.stddev_user_usage_seconds THEN 'Regular User'
                    ELSE 'Light User'
                END as user_category,
                CASE 
                    WHEN aus.session_count >= 50 THEN 'Very High'
                    WHEN aus.session_count >= 20 THEN 'High'
                    WHEN aus.session_count >= 10 THEN 'Medium'
                    WHEN aus.session_count >= 5 THEN 'Low'
                    ELSE 'Very Low'
                END as engagement_level
            FROM aggregated_user_stats aus
            CROSS JOIN total_stats ts
        )
        SELECT 
            user,
            total_seconds,
            session_count,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            avg_stddev_session_seconds,
            first_usage_date,
            last_usage_date,
            total_active_days,
            platforms_used,
            usage_percentage,
            session_percentage,
            usage_rank,
            session_rank,
            usage_quartile,
            user_category,
            engagement_level,
            grand_total_seconds,
            grand_total_sessions,
            total_users,
            avg_user_usage_seconds,
            stddev_user_usage_seconds,
            avg_sessions_per_user,
            stddev_sessions_per_user
        FROM user_analysis
        ORDER BY total_seconds DESC
        LIMIT ?
        """
        
        params.append(limit)
        
        # Execute query
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
                    "tool": "app_users",
                    "description": f"Users who have used {application_name}",
                    "application_name": application_name,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "platform": platform
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "users": []
                },
                "insights": {
                    "summary": f"No users found for application '{application_name}' matching the specified criteria",
                    "recommendations": [
                        "Verify the application name spelling",
                        "Try expanding the date range for analysis",
                        "Check if the specified platform has recorded usage data"
                    ]
                }
            }
        
        # Process results
        users = []
        grand_total_seconds = results[0][18] if results else 0
        grand_total_sessions = results[0][19] if results else 0
        total_users = results[0][20] if results else 0
        avg_user_usage_seconds = results[0][21] if results else 0
        stddev_user_usage_seconds = results[0][22] if results else 0
        avg_sessions_per_user = results[0][23] if results else 0
        stddev_sessions_per_user = results[0][24] if results else 0
        
        for row in results:
            # Calculate additional metrics
            usage_span_days = (datetime.strptime(row[8], '%Y-%m-%d') - 
                             datetime.strptime(row[7], '%Y-%m-%d')).days + 1
            usage_frequency = round((row[9] / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
            sessions_per_day = round(row[2] / row[9], 2) if row[9] > 0 else 0
            
            user_data = {
                "rank": int(row[13]),  # usage_rank
                "user": row[0],
                "usage_metrics": {
                    "total_hours": round(row[1] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[1] / 60, 2),  # total_seconds to minutes
                    "usage_percentage": row[11],  # usage_percentage
                    "usage_quartile": int(row[15]),  # usage_quartile (1=lowest, 4=highest)
                    "user_category": row[16],  # user_category
                    "vs_average_usage": round(((row[1] - avg_user_usage_seconds) / avg_user_usage_seconds) * 100, 1) if avg_user_usage_seconds > 0 else 0
                },
                "session_metrics": {
                    "total_sessions": int(row[2]),
                    "session_percentage": row[12],  # session_percentage
                    "session_rank": int(row[14]),  # session_rank
                    "engagement_level": row[17],  # engagement_level
                    "avg_session_minutes": round(row[3] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[4] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[5] / 60, 2),  # max_session_seconds to minutes
                    "session_variability": round(row[6] / 60, 2) if row[6] else 0,  # avg_stddev_session_seconds to minutes
                    "sessions_per_day": sessions_per_day
                },
                "platform_metrics": {
                    "platforms_used": int(row[10]),
                    "cross_platform": row[10] > 1,
                    "platform_diversity": "High" if row[10] > 2 else "Medium" if row[10] == 2 else "Single"
                },
                "timeline": {
                    "first_usage_date": row[7],
                    "last_usage_date": row[8],
                    "active_days": int(row[9]),
                    "usage_span_days": usage_span_days,
                    "usage_frequency": usage_frequency,
                    "days_since_last_use": (datetime.now().date() - datetime.strptime(row[8], '%Y-%m-%d').date()).days
                }
            }
            users.append(user_data)
        
        # Generate insights
        total_usage_hours = round(grand_total_seconds / 3600, 2)
        
        # User category analysis
        power_users = [user for user in users if user['usage_metrics']['user_category'] == 'Power User']
        heavy_users = [user for user in users if user['usage_metrics']['user_category'] == 'Heavy User']
        regular_users = [user for user in users if user['usage_metrics']['user_category'] == 'Regular User']
        light_users = [user for user in users if user['usage_metrics']['user_category'] == 'Light User']
        
        # Engagement level analysis
        very_high_engagement = [user for user in users if user['session_metrics']['engagement_level'] == 'Very High']
        high_engagement = [user for user in users if user['session_metrics']['engagement_level'] == 'High']
        medium_engagement = [user for user in users if user['session_metrics']['engagement_level'] == 'Medium']
        low_engagement = [user for user in users if user['session_metrics']['engagement_level'] == 'Low']
        very_low_engagement = [user for user in users if user['session_metrics']['engagement_level'] == 'Very Low']
        
        insights = {
            "summary": f"Analysis of {len(users)} users who have used '{application_name}'",
            "key_findings": [],
            "user_distribution": {
                "total_users_analyzed": len(users),
                "total_users_for_app": total_users,
                "total_usage_hours": total_usage_hours,
                "total_sessions": grand_total_sessions,
                "average_usage_per_user_hours": round(avg_user_usage_seconds / 3600, 2),
                "average_sessions_per_user": round(avg_sessions_per_user, 1),
                "user_categories": {
                    "power_users": len(power_users),
                    "heavy_users": len(heavy_users),
                    "regular_users": len(regular_users),
                    "light_users": len(light_users)
                },
                "engagement_levels": {
                    "very_high": len(very_high_engagement),
                    "high": len(high_engagement),
                    "medium": len(medium_engagement),
                    "low": len(low_engagement),
                    "very_low": len(very_low_engagement)
                }
            },
            "recommendations": []
        }
        
        if users:
            top_user = users[0]
            insights["key_findings"].extend([
                f"Top user '{top_user['user']}' has {top_user['usage_metrics']['total_hours']} hours ({top_user['usage_metrics']['usage_percentage']}% of total usage)",
                f"Top user has {top_user['session_metrics']['total_sessions']} sessions with {top_user['session_metrics']['avg_session_minutes']} minutes average session length",
                f"User distribution: {len(power_users)} power users, {len(heavy_users)} heavy users, {len(regular_users)} regular users, {len(light_users)} light users"
            ])
            
            # Usage concentration analysis
            if len(users) >= 5:
                top_5_percentage = sum(user['usage_metrics']['usage_percentage'] for user in users[:5])
                insights["key_findings"].append(f"Top 5 users account for {round(top_5_percentage, 1)}% of total application usage")
                
                if top_5_percentage > 70:
                    insights["recommendations"].append("High usage concentration - consider strategies to engage more users")
                elif top_5_percentage < 40:
                    insights["recommendations"].append("Well-distributed usage across users - good user engagement balance")
        
        # Engagement recommendations
        if power_users or heavy_users:
            total_engaged = len(power_users) + len(heavy_users)
            insights["recommendations"].append(f"Leverage {total_engaged} highly engaged users as advocates and feedback sources")
        
        if light_users:
            insights["recommendations"].append(f"Develop engagement strategies for {len(light_users)} light users to increase adoption")
        
        # Platform diversity recommendations
        cross_platform_users = [user for user in users if user['platform_metrics']['cross_platform']]
        if cross_platform_users:
            insights["recommendations"].append(f"Study {len(cross_platform_users)} cross-platform users for insights on multi-platform workflows")
        
        # Retention recommendations
        recent_users = [user for user in users if user['timeline']['days_since_last_use'] <= 7]
        if recent_users:
            insights["recommendations"].append(f"Focus retention efforts on {len(recent_users)} recently active users")
        
        return {
            "status": "success",
            "data": {
                "tool": "app_users",
                "description": f"Comprehensive analysis of users who have used '{application_name}'",
                "application_name": application_name,
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit,
                    "platform": platform
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(users),
                "users": users
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in app_users: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze users for application '{application_name}': {str(e)}",
            "tool": "app_users"
        }
