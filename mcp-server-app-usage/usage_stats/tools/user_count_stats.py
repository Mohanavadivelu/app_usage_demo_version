"""
Tool: User Count Stats
Category: Usage Stats
Feature ID: 64

Description:
    Comprehensive user count statistics with detailed analytics and insights

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of applications to return (default: 100, max: 1000)
    - min_users (int, optional): Minimum number of users to include application (default: 1)
    - platform (str, optional): Platform to filter by

Returns:
    - Comprehensive user count statistics with detailed analytics and insights

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
async def user_count_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    min_users: Optional[int] = 1,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive user count statistics with detailed analytics and insights.
    
    Provides detailed insights into user adoption and engagement patterns, including:
    - User count per application
    - User engagement classification
    - Platform distribution analysis
    - Session and usage patterns
    - User retention and activity metrics
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        limit: Maximum number of applications to return (1-1000, default: 100)
        min_users: Minimum number of users to include application (default: 1)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
    
    Returns:
        Dict containing comprehensive user count statistics with analytics and insights
    """
    try:
        # Parameter validation
        if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > 1000):
            return {
                "status": "error",
                "message": "limit must be an integer between 1 and 1000"
            }
        
        if min_users is not None and (not isinstance(min_users, int) or min_users < 1):
            return {
                "status": "error", 
                "message": "min_users must be a positive integer"
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
        min_users = min_users or 1
        
        # Build query with CTEs for comprehensive analysis
        query = """
        WITH app_user_stats AS (
            SELECT 
                application_name,
                platform,
                COUNT(DISTINCT user) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_seconds) as total_seconds,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds,
                MIN(log_date) as first_usage_date,
                MAX(log_date) as last_usage_date,
                COUNT(DISTINCT log_date) as active_days,
                COUNT(DISTINCT platform) as platforms_used
            FROM app_usage
            WHERE 1=1
        """
        
        params = []
        
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
            GROUP BY application_name, platform
            HAVING COUNT(DISTINCT user) >= ?
        ),
        total_stats AS (
            SELECT 
                COUNT(DISTINCT user) as total_unique_users,
                SUM(total_seconds) as grand_total_seconds,
                SUM(total_sessions) as grand_total_sessions,
                COUNT(*) as total_apps,
                AVG(unique_users) as avg_users_per_app,
                STDDEV(unique_users) as stddev_users_per_app
            FROM (
                SELECT user, SUM(total_seconds) as total_seconds, SUM(total_sessions) as total_sessions
                FROM app_user_stats
                GROUP BY user
            )
        ),
        user_engagement_analysis AS (
            SELECT 
                aus.*,
                ts.total_unique_users,
                ts.grand_total_seconds,
                ts.grand_total_sessions,
                ts.total_apps,
                ts.avg_users_per_app,
                ts.stddev_users_per_app,
                ROUND((aus.unique_users * 100.0 / ts.total_unique_users), 2) as user_market_share,
                ROUND((aus.total_seconds * 100.0 / ts.grand_total_seconds), 2) as usage_share,
                ROUND((aus.total_sessions * 100.0 / ts.grand_total_sessions), 2) as session_share,
                ROUND((aus.total_sessions / aus.unique_users), 2) as sessions_per_user,
                ROUND((aus.total_seconds / aus.unique_users), 2) as avg_usage_per_user_seconds,
                ROUND((aus.active_days / aus.unique_users), 2) as avg_active_days_per_user,
                ROW_NUMBER() OVER (ORDER BY aus.unique_users DESC) as user_rank,
                NTILE(4) OVER (ORDER BY aus.unique_users) as user_quartile,
                CASE 
                    WHEN aus.unique_users >= 50 THEN 'Very High'
                    WHEN aus.unique_users >= 20 THEN 'High'
                    WHEN aus.unique_users >= 10 THEN 'Medium'
                    WHEN aus.unique_users >= 5 THEN 'Low'
                    ELSE 'Very Low'
                END as user_adoption_level,
                CASE 
                    WHEN (aus.total_sessions / aus.unique_users) >= 10 THEN 'Highly Engaged'
                    WHEN (aus.total_sessions / aus.unique_users) >= 5 THEN 'Engaged'
                    WHEN (aus.total_sessions / aus.unique_users) >= 2 THEN 'Moderately Engaged'
                    ELSE 'Low Engagement'
                END as engagement_level
            FROM app_user_stats aus
            CROSS JOIN total_stats ts
        )
        SELECT 
            application_name,
            platform,
            unique_users,
            total_sessions,
            total_seconds,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            first_usage_date,
            last_usage_date,
            active_days,
            platforms_used,
            user_market_share,
            usage_share,
            session_share,
            sessions_per_user,
            avg_usage_per_user_seconds,
            avg_active_days_per_user,
            user_rank,
            user_quartile,
            user_adoption_level,
            engagement_level,
            total_unique_users,
            grand_total_seconds,
            grand_total_sessions,
            total_apps,
            avg_users_per_app,
            stddev_users_per_app
        FROM user_engagement_analysis
        ORDER BY unique_users DESC
        LIMIT ?
        """
        
        params.extend([min_users, limit])
        
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
                    "tool": "user_count_stats",
                    "description": "Comprehensive user count statistics",
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "min_users": min_users,
                        "platform": platform
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "applications": []
                },
                "insights": {
                    "summary": "No applications found matching the specified criteria",
                    "recommendations": [
                        "Try expanding the date range for analysis",
                        "Reduce the minimum user count filter",
                        "Check if the specified platform has recorded user data"
                    ]
                }
            }
        
        # Process results
        applications = []
        total_unique_users = results[0][22] if results else 0
        grand_total_seconds = results[0][23] if results else 0
        grand_total_sessions = results[0][24] if results else 0
        total_apps_in_db = results[0][25] if results else 0
        avg_users_per_app = results[0][26] if results else 0
        stddev_users_per_app = results[0][27] if results else 0
        
        for row in results:
            # Calculate additional metrics
            usage_span_days = (datetime.strptime(row[9], '%Y-%m-%d') - 
                             datetime.strptime(row[8], '%Y-%m-%d')).days + 1
            user_retention_rate = round((row[10] / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
            
            app_data = {
                "rank": int(row[18]),  # user_rank
                "application_name": row[0],
                "platform": row[1],
                "user_metrics": {
                    "unique_users": int(row[2]),
                    "user_market_share": row[12],  # user_market_share
                    "user_quartile": int(row[19]),  # user_quartile (1=lowest, 4=highest)
                    "user_adoption_level": row[20],  # user_adoption_level
                    "avg_active_days_per_user": round(row[17], 2),  # avg_active_days_per_user
                    "user_retention_rate": user_retention_rate
                },
                "engagement_metrics": {
                    "engagement_level": row[21],  # engagement_level
                    "sessions_per_user": round(row[15], 2),  # sessions_per_user
                    "avg_usage_per_user_hours": round(row[16] / 3600, 2),  # avg_usage_per_user_seconds to hours
                    "avg_usage_per_user_minutes": round(row[16] / 60, 2),  # avg_usage_per_user_seconds to minutes
                    "total_sessions": int(row[3]),
                    "session_share": row[14]  # session_share
                },
                "usage_metrics": {
                    "total_hours": round(row[4] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[4] / 60, 2),  # total_seconds to minutes
                    "usage_share": row[13],  # usage_share
                    "avg_session_minutes": round(row[5] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[6] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[7] / 60, 2)  # max_session_seconds to minutes
                },
                "platform_metrics": {
                    "platforms_used": int(row[11]),
                    "cross_platform": row[11] > 1,
                    "platform_diversity": "High" if row[11] > 2 else "Medium" if row[11] == 2 else "Single"
                },
                "timeline": {
                    "first_usage_date": row[8],
                    "last_usage_date": row[9],
                    "active_days": int(row[10]),
                    "usage_span_days": usage_span_days,
                    "usage_consistency": round((row[10] / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
                }
            }
            applications.append(app_data)
        
        # Generate insights
        total_usage_hours = round(grand_total_seconds / 3600, 2)
        
        # Adoption level analysis
        very_high_adoption = [app for app in applications if app['user_metrics']['user_adoption_level'] == 'Very High']
        high_adoption = [app for app in applications if app['user_metrics']['user_adoption_level'] == 'High']
        medium_adoption = [app for app in applications if app['user_metrics']['user_adoption_level'] == 'Medium']
        low_adoption = [app for app in applications if app['user_metrics']['user_adoption_level'] == 'Low']
        very_low_adoption = [app for app in applications if app['user_metrics']['user_adoption_level'] == 'Very Low']
        
        # Engagement level analysis
        highly_engaged = [app for app in applications if app['engagement_metrics']['engagement_level'] == 'Highly Engaged']
        engaged = [app for app in applications if app['engagement_metrics']['engagement_level'] == 'Engaged']
        moderately_engaged = [app for app in applications if app['engagement_metrics']['engagement_level'] == 'Moderately Engaged']
        low_engagement = [app for app in applications if app['engagement_metrics']['engagement_level'] == 'Low Engagement']
        
        insights = {
            "summary": f"Analysis of {len(applications)} applications showing comprehensive user count statistics",
            "key_findings": [],
            "user_adoption_analysis": {
                "total_unique_users_in_system": total_unique_users,
                "total_usage_hours": total_usage_hours,
                "total_sessions": grand_total_sessions,
                "average_users_per_app": round(avg_users_per_app, 1),
                "user_distribution_std_dev": round(stddev_users_per_app, 1) if stddev_users_per_app else 0,
                "adoption_levels": {
                    "very_high": len(very_high_adoption),
                    "high": len(high_adoption),
                    "medium": len(medium_adoption),
                    "low": len(low_adoption),
                    "very_low": len(very_low_adoption)
                }
            },
            "engagement_analysis": {
                "engagement_levels": {
                    "highly_engaged": len(highly_engaged),
                    "engaged": len(engaged),
                    "moderately_engaged": len(moderately_engaged),
                    "low_engagement": len(low_engagement)
                }
            },
            "recommendations": []
        }
        
        if applications:
            top_app = applications[0]
            insights["key_findings"].extend([
                f"'{top_app['application_name']}' leads with {top_app['user_metrics']['unique_users']} users ({top_app['user_metrics']['user_market_share']}% market share)",
                f"Top application users average {top_app['engagement_metrics']['sessions_per_user']} sessions and {top_app['engagement_metrics']['avg_usage_per_user_hours']} hours each",
                f"User adoption distribution: {len(very_high_adoption)} very high, {len(high_adoption)} high, {len(medium_adoption)} medium, {len(low_adoption)} low, {len(very_low_adoption)} very low"
            ])
            
            # Market concentration analysis
            if len(applications) >= 3:
                top_3_market_share = sum(app['user_metrics']['user_market_share'] for app in applications[:3])
                insights["key_findings"].append(f"Top 3 applications capture {round(top_3_market_share, 1)}% of total users")
                
                if top_3_market_share > 70:
                    insights["recommendations"].append("High user concentration in top apps - consider strategies to diversify user engagement")
                elif top_3_market_share < 40:
                    insights["recommendations"].append("Well-distributed user base - good market diversity")
        
        # Engagement recommendations
        if highly_engaged or engaged:
            total_engaged = len(highly_engaged) + len(engaged)
            insights["recommendations"].append(f"Leverage {total_engaged} highly engaged applications as success models")
        
        if low_engagement:
            insights["recommendations"].append(f"Improve engagement for {len(low_engagement)} applications with low user interaction")
        
        # Platform diversity recommendations
        cross_platform_apps = [app for app in applications if app['platform_metrics']['cross_platform']]
        if cross_platform_apps:
            insights["recommendations"].append(f"Promote {len(cross_platform_apps)} cross-platform applications for broader reach")
        
        # Retention recommendations
        high_retention_apps = [app for app in applications if app['timeline']['usage_consistency'] > 70]
        if high_retention_apps:
            insights["recommendations"].append(f"Study {len(high_retention_apps)} applications with high user retention (>70% consistency)")
        
        return {
            "status": "success",
            "data": {
                "tool": "user_count_stats",
                "description": "Comprehensive user count statistics with detailed analytics",
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit,
                    "min_users": min_users,
                    "platform": platform
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(applications),
                "applications": applications
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_count_stats: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze user count statistics: {str(e)}",
            "tool": "user_count_stats"
        }
