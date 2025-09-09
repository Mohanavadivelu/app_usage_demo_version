"""
Tool: Top Apps By Usage
Category: Usage Stats
Feature ID: 60

Description:
    Rank applications by total usage time with comprehensive analytics

Parameters:
    - top_n (int, optional): Number of top results (default: 10, max: 100)
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - platform (str, optional): Platform to filter by
    - min_usage_minutes (int, optional): Minimum usage time in minutes to include

Returns:
    - Ranked applications by total usage time with detailed analytics and insights

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
async def top_apps_by_usage(
    top_n: Optional[int] = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    min_usage_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Rank applications by total usage time with comprehensive analytics.
    
    Provides detailed insights into application usage patterns, including:
    - Total usage time per application
    - User engagement metrics
    - Session statistics
    - Market share analysis
    - Usage trends and recommendations
    
    Args:
        top_n: Number of top applications to return (1-100, default: 10)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
        min_usage_minutes: Minimum usage time in minutes to include apps
    
    Returns:
        Dict containing ranked applications with usage analytics and insights
    """
    try:
        # Parameter validation
        if top_n is not None and (not isinstance(top_n, int) or top_n < 1 or top_n > 100):
            return {
                "status": "error",
                "message": "top_n must be an integer between 1 and 100"
            }
        
        if min_usage_minutes is not None and (not isinstance(min_usage_minutes, int) or min_usage_minutes < 0):
            return {
                "status": "error", 
                "message": "min_usage_minutes must be a non-negative integer"
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
        min_usage_seconds = (min_usage_minutes * 60) if min_usage_minutes else 0
        
        # Build query with CTEs for comprehensive analysis
        query = """
        WITH app_usage_stats AS (
            SELECT 
                application_name,
                platform,
                SUM(duration_seconds) as total_seconds,
                COUNT(DISTINCT user) as unique_users,
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds,
                MIN(log_date) as first_usage_date,
                MAX(log_date) as last_usage_date
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
            HAVING SUM(duration_seconds) >= ?
        ),
        total_stats AS (
            SELECT 
                SUM(total_seconds) as grand_total_seconds,
                SUM(unique_users) as grand_total_users,
                SUM(total_sessions) as grand_total_sessions,
                COUNT(*) as total_apps
            FROM app_usage_stats
        ),
        ranked_apps AS (
            SELECT 
                aus.*,
                ts.grand_total_seconds,
                ts.grand_total_users,
                ts.grand_total_sessions,
                ts.total_apps,
                ROUND((aus.total_seconds * 100.0 / ts.grand_total_seconds), 2) as usage_percentage,
                ROUND((aus.unique_users * 100.0 / ts.grand_total_users), 2) as user_percentage,
                ROW_NUMBER() OVER (ORDER BY aus.total_seconds DESC) as usage_rank,
                ROW_NUMBER() OVER (ORDER BY aus.unique_users DESC) as user_rank,
                ROW_NUMBER() OVER (ORDER BY aus.avg_session_seconds DESC) as engagement_rank
            FROM app_usage_stats aus
            CROSS JOIN total_stats ts
        )
        SELECT 
            application_name,
            platform,
            total_seconds,
            unique_users,
            total_sessions,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            first_usage_date,
            last_usage_date,
            usage_percentage,
            user_percentage,
            usage_rank,
            user_rank,
            engagement_rank,
            grand_total_seconds,
            grand_total_users,
            grand_total_sessions,
            total_apps
        FROM ranked_apps
        ORDER BY total_seconds DESC
        LIMIT ?
        """
        
        params.extend([min_usage_seconds, top_n])
        
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
                    "tool": "top_apps_by_usage",
                    "description": "Rank applications by total usage time",
                    "parameters": {
                        "top_n": top_n,
                        "start_date": start_date,
                        "end_date": end_date,
                        "platform": platform,
                        "min_usage_minutes": min_usage_minutes
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "applications": []
                },
                "insights": {
                    "summary": "No applications found matching the specified criteria",
                    "recommendations": [
                        "Try expanding the date range for analysis",
                        "Remove or reduce the minimum usage time filter",
                        "Check if the specified platform has recorded usage data"
                    ]
                }
            }
        
        # Process results
        applications = []
        total_usage_time = results[0][15] if results else 0  # grand_total_seconds
        total_users = results[0][16] if results else 0  # grand_total_users
        total_sessions = results[0][17] if results else 0  # grand_total_sessions
        total_apps_in_db = results[0][18] if results else 0  # total_apps
        
        for row in results:
            app_data = {
                "rank": int(row[12]),  # usage_rank
                "application_name": row[0],
                "platform": row[1],
                "usage_metrics": {
                    "total_hours": round(row[2] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[2] / 60, 2),  # total_seconds to minutes
                    "usage_percentage": row[10],  # usage_percentage
                    "market_share_rank": int(row[12])  # usage_rank
                },
                "user_metrics": {
                    "unique_users": int(row[3]),
                    "user_percentage": row[11],  # user_percentage
                    "user_popularity_rank": int(row[13])  # user_rank
                },
                "session_metrics": {
                    "total_sessions": int(row[4]),
                    "avg_session_minutes": round(row[5] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[6] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[7] / 60, 2),  # max_session_seconds to minutes
                    "sessions_per_user": round(row[4] / row[3], 2) if row[3] > 0 else 0,
                    "engagement_rank": int(row[14])  # engagement_rank
                },
                "timeline": {
                    "first_usage_date": row[8],
                    "last_usage_date": row[9],
                    "days_active": (datetime.strptime(row[9], '%Y-%m-%d') - 
                                  datetime.strptime(row[8], '%Y-%m-%d')).days + 1
                }
            }
            applications.append(app_data)
        
        # Generate insights
        top_app = applications[0] if applications else None
        avg_usage_hours = round(total_usage_time / 3600 / len(applications), 2) if applications else 0
        
        insights = {
            "summary": f"Analysis of top {len(applications)} applications by usage time",
            "key_findings": [],
            "market_analysis": {
                "total_usage_hours": round(total_usage_time / 3600, 2),
                "total_unique_users": total_users,
                "total_sessions": total_sessions,
                "average_usage_per_app_hours": avg_usage_hours,
                "apps_analyzed": len(applications),
                "total_apps_in_database": total_apps_in_db
            },
            "recommendations": []
        }
        
        if top_app:
            insights["key_findings"].extend([
                f"'{top_app['application_name']}' is the most used application with {top_app['usage_metrics']['total_hours']} hours ({top_app['usage_metrics']['usage_percentage']}% of total usage)",
                f"Top application has {top_app['user_metrics']['unique_users']} unique users ({top_app['user_metrics']['user_percentage']}% of total users)",
                f"Average session length for top app: {top_app['session_metrics']['avg_session_minutes']} minutes"
            ])
            
            # Market concentration analysis
            if len(applications) >= 3:
                top_3_percentage = sum(app['usage_metrics']['usage_percentage'] for app in applications[:3])
                insights["key_findings"].append(f"Top 3 applications account for {round(top_3_percentage, 1)}% of total usage time")
                
                if top_3_percentage > 60:
                    insights["recommendations"].append("Market shows high concentration - consider diversifying application portfolio")
                elif top_3_percentage < 30:
                    insights["recommendations"].append("Usage is well-distributed across applications - good diversity")
        
        # Usage pattern recommendations
        if applications:
            high_engagement_apps = [app for app in applications if app['session_metrics']['avg_session_minutes'] > 30]
            if high_engagement_apps:
                insights["recommendations"].append(f"Focus on {len(high_engagement_apps)} high-engagement applications (>30 min avg sessions)")
            
            multi_user_apps = [app for app in applications if app['user_metrics']['unique_users'] > 10]
            if multi_user_apps:
                insights["recommendations"].append(f"Prioritize {len(multi_user_apps)} applications with broad user adoption (>10 users)")
        
        return {
            "status": "success",
            "data": {
                "tool": "top_apps_by_usage",
                "description": "Rank applications by total usage time with comprehensive analytics",
                "parameters": {
                    "top_n": top_n,
                    "start_date": start_date,
                    "end_date": end_date,
                    "platform": platform,
                    "min_usage_minutes": min_usage_minutes
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(applications),
                "applications": applications
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in top_apps_by_usage: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze top applications by usage: {str(e)}",
            "tool": "top_apps_by_usage"
        }
