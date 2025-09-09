"""
Tool: Top Apps By Users
Category: Usage Stats
Feature ID: 61

Description:
    Rank applications by number of unique users with comprehensive analytics

Parameters:
    - top_n (int, optional): Number of top results (default: 10, max: 100)
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - platform (str, optional): Platform to filter by
    - min_users (int, optional): Minimum user count to include applications

Returns:
    - Ranked applications by unique user count with detailed analytics and insights

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
async def top_apps_by_users(
    top_n: Optional[int] = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    min_users: Optional[int] = None
) -> Dict[str, Any]:
    """
    Rank applications by number of unique users with comprehensive analytics.
    
    Provides detailed insights into application popularity and user adoption, including:
    - User adoption metrics per application
    - Usage intensity analysis
    - Market penetration statistics
    - User engagement patterns
    - Strategic recommendations for user growth
    
    Args:
        top_n: Number of top applications to return (1-100, default: 10)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
        min_users: Minimum number of unique users to include applications
    
    Returns:
        Dict containing ranked applications with user adoption analytics and insights
    """
    try:
        # Parameter validation
        if top_n is not None and (not isinstance(top_n, int) or top_n < 1 or top_n > 100):
            return {
                "status": "error",
                "message": "top_n must be an integer between 1 and 100"
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
        top_n = top_n or 10
        min_users = min_users or 1
        
        # Build query with CTEs for comprehensive analysis
        query = """
        WITH app_user_stats AS (
            SELECT 
                application_name,
                platform,
                COUNT(DISTINCT user) as unique_users,
                SUM(duration_seconds) as total_seconds,
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds,
                MIN(log_date) as first_usage_date,
                MAX(log_date) as last_usage_date,
                COUNT(DISTINCT log_date) as active_days
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
                COUNT(*) as total_apps
            FROM (
                SELECT user, SUM(total_seconds) as total_seconds, SUM(total_sessions) as total_sessions
                FROM app_user_stats
                GROUP BY user
            )
        ),
        user_engagement_stats AS (
            SELECT 
                aus.*,
                ts.total_unique_users,
                ts.grand_total_seconds,
                ts.grand_total_sessions,
                ts.total_apps,
                ROUND((aus.unique_users * 100.0 / ts.total_unique_users), 2) as user_penetration_percentage,
                ROUND((aus.total_seconds * 100.0 / ts.grand_total_seconds), 2) as usage_share_percentage,
                ROUND((aus.total_seconds / aus.unique_users), 2) as avg_usage_per_user_seconds,
                ROUND((aus.total_sessions / aus.unique_users), 2) as avg_sessions_per_user,
                ROW_NUMBER() OVER (ORDER BY aus.unique_users DESC) as user_rank,
                ROW_NUMBER() OVER (ORDER BY aus.total_seconds DESC) as usage_rank,
                ROW_NUMBER() OVER (ORDER BY aus.avg_session_seconds DESC) as engagement_rank
            FROM app_user_stats aus
            CROSS JOIN total_stats ts
        )
        SELECT 
            application_name,
            platform,
            unique_users,
            total_seconds,
            total_sessions,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            first_usage_date,
            last_usage_date,
            active_days,
            user_penetration_percentage,
            usage_share_percentage,
            avg_usage_per_user_seconds,
            avg_sessions_per_user,
            user_rank,
            usage_rank,
            engagement_rank,
            total_unique_users,
            grand_total_seconds,
            grand_total_sessions,
            total_apps
        FROM user_engagement_stats
        ORDER BY unique_users DESC
        LIMIT ?
        """
        
        params.extend([min_users, top_n])
        
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
                    "tool": "top_apps_by_users",
                    "description": "Rank applications by number of unique users",
                    "parameters": {
                        "top_n": top_n,
                        "start_date": start_date,
                        "end_date": end_date,
                        "platform": platform,
                        "min_users": min_users
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
        total_unique_users = results[0][18] if results else 0
        grand_total_seconds = results[0][19] if results else 0
        grand_total_sessions = results[0][20] if results else 0
        total_apps_in_db = results[0][21] if results else 0
        
        for row in results:
            app_data = {
                "rank": int(row[15]),  # user_rank
                "application_name": row[0],
                "platform": row[1],
                "user_metrics": {
                    "unique_users": int(row[2]),
                    "user_penetration_percentage": row[11],  # user_penetration_percentage
                    "user_popularity_rank": int(row[15]),  # user_rank
                    "avg_usage_per_user_hours": round(row[13] / 3600, 2),  # avg_usage_per_user_seconds to hours
                    "avg_sessions_per_user": round(row[14], 2)  # avg_sessions_per_user
                },
                "usage_metrics": {
                    "total_hours": round(row[3] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[3] / 60, 2),  # total_seconds to minutes
                    "usage_share_percentage": row[12],  # usage_share_percentage
                    "usage_intensity_rank": int(row[16])  # usage_rank
                },
                "session_metrics": {
                    "total_sessions": int(row[4]),
                    "avg_session_minutes": round(row[5] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[6] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[7] / 60, 2),  # max_session_seconds to minutes
                    "engagement_rank": int(row[17])  # engagement_rank
                },
                "timeline": {
                    "first_usage_date": row[8],
                    "last_usage_date": row[9],
                    "active_days": int(row[10]),
                    "days_since_first_use": (datetime.strptime(row[9], '%Y-%m-%d') - 
                                           datetime.strptime(row[8], '%Y-%m-%d')).days + 1
                }
            }
            applications.append(app_data)
        
        # Generate insights
        top_app = applications[0] if applications else None
        avg_users_per_app = round(sum(app['user_metrics']['unique_users'] for app in applications) / len(applications), 1) if applications else 0
        
        insights = {
            "summary": f"Analysis of top {len(applications)} applications by unique user count",
            "key_findings": [],
            "user_adoption_analysis": {
                "total_unique_users_in_system": total_unique_users,
                "total_usage_hours": round(grand_total_seconds / 3600, 2),
                "total_sessions": grand_total_sessions,
                "average_users_per_app": avg_users_per_app,
                "apps_analyzed": len(applications),
                "total_apps_in_database": total_apps_in_db
            },
            "recommendations": []
        }
        
        if top_app:
            insights["key_findings"].extend([
                f"'{top_app['application_name']}' has the highest user adoption with {top_app['user_metrics']['unique_users']} unique users ({top_app['user_metrics']['user_penetration_percentage']}% market penetration)",
                f"Top application users spend an average of {top_app['user_metrics']['avg_usage_per_user_hours']} hours each",
                f"Each user of the top app has {top_app['user_metrics']['avg_sessions_per_user']} sessions on average"
            ])
            
            # User concentration analysis
            if len(applications) >= 3:
                top_3_user_percentage = sum(app['user_metrics']['user_penetration_percentage'] for app in applications[:3])
                insights["key_findings"].append(f"Top 3 applications capture {round(top_3_user_percentage, 1)}% of total users")
                
                if top_3_user_percentage > 70:
                    insights["recommendations"].append("High user concentration in top apps - consider strategies to diversify user engagement")
                elif top_3_user_percentage < 40:
                    insights["recommendations"].append("Well-distributed user base across applications - good market diversity")
        
        # User engagement recommendations
        if applications:
            high_engagement_apps = [app for app in applications if app['user_metrics']['avg_usage_per_user_hours'] > 5]
            if high_engagement_apps:
                insights["recommendations"].append(f"Focus on {len(high_engagement_apps)} high-engagement applications (>5 hours per user)")
            
            broad_adoption_apps = [app for app in applications if app['user_metrics']['user_penetration_percentage'] > 10]
            if broad_adoption_apps:
                insights["recommendations"].append(f"Leverage {len(broad_adoption_apps)} applications with broad market penetration (>10% users)")
            
            # Session frequency analysis
            frequent_use_apps = [app for app in applications if app['user_metrics']['avg_sessions_per_user'] > 5]
            if frequent_use_apps:
                insights["recommendations"].append(f"Promote {len(frequent_use_apps)} applications with high user retention (>5 sessions per user)")
        
        return {
            "status": "success",
            "data": {
                "tool": "top_apps_by_users",
                "description": "Rank applications by number of unique users with comprehensive analytics",
                "parameters": {
                    "top_n": top_n,
                    "start_date": start_date,
                    "end_date": end_date,
                    "platform": platform,
                    "min_users": min_users
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(applications),
                "applications": applications
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in top_apps_by_users: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze top applications by users: {str(e)}",
            "tool": "top_apps_by_users"
        }
