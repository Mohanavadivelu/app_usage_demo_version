"""
Tool: Usage Time Stats
Category: Usage Stats
Feature ID: 63

Description:
    Comprehensive usage time statistics with detailed analytics and insights

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of applications to return (default: 100, max: 1000)
    - platform (str, optional): Platform to filter by
    - min_usage_hours (float, optional): Minimum usage hours to include applications

Returns:
    - Comprehensive usage time statistics with detailed analytics and insights

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
async def usage_time_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    platform: Optional[str] = None,
    min_usage_hours: Optional[float] = None
) -> Dict[str, Any]:
    """
    Comprehensive usage time statistics with detailed analytics and insights.
    
    Provides detailed insights into application usage patterns, including:
    - Total usage time per application
    - Usage distribution and percentages
    - Session statistics and patterns
    - User engagement metrics
    - Statistical analysis and recommendations
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        limit: Maximum number of applications to return (1-1000, default: 100)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
        min_usage_hours: Minimum usage hours to include applications
    
    Returns:
        Dict containing comprehensive usage time statistics with analytics and insights
    """
    try:
        # Parameter validation
        if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > 1000):
            return {
                "status": "error",
                "message": "limit must be an integer between 1 and 1000"
            }
        
        if min_usage_hours is not None and (not isinstance(min_usage_hours, (int, float)) or min_usage_hours < 0):
            return {
                "status": "error", 
                "message": "min_usage_hours must be a non-negative number"
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
        min_usage_seconds = (min_usage_hours * 3600) if min_usage_hours else 0
        
        # Build query with CTEs for comprehensive analysis
        query = """
        WITH app_usage_stats AS (
            SELECT 
                application_name,
                platform,
                SUM(duration_seconds) as total_seconds,
                COUNT(*) as total_sessions,
                COUNT(DISTINCT user) as unique_users,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds,
                STDDEV(duration_seconds) as stddev_session_seconds,
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
            HAVING SUM(duration_seconds) >= ?
        ),
        total_stats AS (
            SELECT 
                SUM(total_seconds) as grand_total_seconds,
                SUM(unique_users) as grand_total_users,
                SUM(total_sessions) as grand_total_sessions,
                COUNT(*) as total_apps,
                AVG(total_seconds) as avg_app_usage_seconds,
                STDDEV(total_seconds) as stddev_app_usage_seconds
            FROM app_usage_stats
        ),
        usage_percentiles AS (
            SELECT 
                aus.*,
                ts.grand_total_seconds,
                ts.grand_total_users,
                ts.grand_total_sessions,
                ts.total_apps,
                ts.avg_app_usage_seconds,
                ts.stddev_app_usage_seconds,
                ROUND((aus.total_seconds * 100.0 / ts.grand_total_seconds), 2) as usage_percentage,
                ROUND((aus.unique_users * 100.0 / ts.grand_total_users), 2) as user_percentage,
                ROUND((aus.total_sessions * 100.0 / ts.grand_total_sessions), 2) as session_percentage,
                ROW_NUMBER() OVER (ORDER BY aus.total_seconds DESC) as usage_rank,
                NTILE(4) OVER (ORDER BY aus.total_seconds) as usage_quartile,
                CASE 
                    WHEN aus.total_seconds > ts.avg_app_usage_seconds + ts.stddev_app_usage_seconds THEN 'High'
                    WHEN aus.total_seconds < ts.avg_app_usage_seconds - ts.stddev_app_usage_seconds THEN 'Low'
                    ELSE 'Medium'
                END as usage_category
            FROM app_usage_stats aus
            CROSS JOIN total_stats ts
        )
        SELECT 
            application_name,
            platform,
            total_seconds,
            total_sessions,
            unique_users,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            stddev_session_seconds,
            first_usage_date,
            last_usage_date,
            active_days,
            usage_percentage,
            user_percentage,
            session_percentage,
            usage_rank,
            usage_quartile,
            usage_category,
            grand_total_seconds,
            grand_total_users,
            grand_total_sessions,
            total_apps,
            avg_app_usage_seconds,
            stddev_app_usage_seconds
        FROM usage_percentiles
        ORDER BY total_seconds DESC
        LIMIT ?
        """
        
        params.extend([min_usage_seconds, limit])
        
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
                    "tool": "usage_time_stats",
                    "description": "Comprehensive usage time statistics",
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "platform": platform,
                        "min_usage_hours": min_usage_hours
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "applications": []
                },
                "insights": {
                    "summary": "No applications found matching the specified criteria",
                    "recommendations": [
                        "Try expanding the date range for analysis",
                        "Remove or reduce the minimum usage hours filter",
                        "Check if the specified platform has recorded usage data"
                    ]
                }
            }
        
        # Process results
        applications = []
        grand_total_seconds = results[0][18] if results else 0
        grand_total_users = results[0][19] if results else 0
        grand_total_sessions = results[0][20] if results else 0
        total_apps_in_db = results[0][21] if results else 0
        avg_app_usage_seconds = results[0][22] if results else 0
        stddev_app_usage_seconds = results[0][23] if results else 0
        
        for row in results:
            # Calculate additional metrics
            usage_intensity = "High" if row[2] > avg_app_usage_seconds + stddev_app_usage_seconds else "Low" if row[2] < avg_app_usage_seconds - stddev_app_usage_seconds else "Medium"
            sessions_per_day = round(row[3] / row[11], 2) if row[11] > 0 else 0
            users_per_day = round(row[4] / row[11], 2) if row[11] > 0 else 0
            
            app_data = {
                "rank": int(row[15]),  # usage_rank
                "application_name": row[0],
                "platform": row[1],
                "usage_metrics": {
                    "total_hours": round(row[2] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[2] / 60, 2),  # total_seconds to minutes
                    "usage_percentage": row[12],  # usage_percentage
                    "usage_quartile": int(row[16]),  # usage_quartile (1=lowest, 4=highest)
                    "usage_category": row[17],  # usage_category
                    "usage_intensity": usage_intensity
                },
                "session_metrics": {
                    "total_sessions": int(row[3]),
                    "session_percentage": row[14],  # session_percentage
                    "avg_session_minutes": round(row[5] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[6] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[7] / 60, 2),  # max_session_seconds to minutes
                    "session_variability": round(row[8] / 60, 2) if row[8] else 0,  # stddev_session_seconds to minutes
                    "sessions_per_day": sessions_per_day
                },
                "user_metrics": {
                    "unique_users": int(row[4]),
                    "user_percentage": row[13],  # user_percentage
                    "sessions_per_user": round(row[3] / row[4], 2) if row[4] > 0 else 0,
                    "avg_usage_per_user_hours": round(row[2] / row[4] / 3600, 2) if row[4] > 0 else 0,
                    "users_per_day": users_per_day
                },
                "timeline": {
                    "first_usage_date": row[9],
                    "last_usage_date": row[10],
                    "active_days": int(row[11]),
                    "usage_span_days": (datetime.strptime(row[10], '%Y-%m-%d') - 
                                      datetime.strptime(row[9], '%Y-%m-%d')).days + 1,
                    "usage_frequency": round((row[11] / ((datetime.strptime(row[10], '%Y-%m-%d') - 
                                                        datetime.strptime(row[9], '%Y-%m-%d')).days + 1)) * 100, 1)
                }
            }
            applications.append(app_data)
        
        # Generate insights
        total_usage_hours = round(grand_total_seconds / 3600, 2)
        avg_usage_per_app = round(total_usage_hours / len(applications), 2) if applications else 0
        
        # Category analysis
        high_usage_apps = [app for app in applications if app['usage_metrics']['usage_category'] == 'High']
        medium_usage_apps = [app for app in applications if app['usage_metrics']['usage_category'] == 'Medium']
        low_usage_apps = [app for app in applications if app['usage_metrics']['usage_category'] == 'Low']
        
        # Quartile analysis
        top_quartile_apps = [app for app in applications if app['usage_metrics']['usage_quartile'] == 4]
        
        insights = {
            "summary": f"Analysis of {len(applications)} applications showing comprehensive usage time statistics",
            "key_findings": [],
            "usage_distribution": {
                "total_usage_hours": total_usage_hours,
                "average_usage_per_app_hours": avg_usage_per_app,
                "high_usage_apps": len(high_usage_apps),
                "medium_usage_apps": len(medium_usage_apps),
                "low_usage_apps": len(low_usage_apps),
                "top_quartile_apps": len(top_quartile_apps)
            },
            "statistical_analysis": {
                "total_applications_analyzed": len(applications),
                "total_applications_in_database": total_apps_in_db,
                "total_unique_users": grand_total_users,
                "total_sessions": grand_total_sessions,
                "average_app_usage_hours": round(avg_app_usage_seconds / 3600, 2),
                "usage_standard_deviation_hours": round(stddev_app_usage_seconds / 3600, 2) if stddev_app_usage_seconds else 0
            },
            "recommendations": []
        }
        
        if applications:
            top_app = applications[0]
            insights["key_findings"].extend([
                f"'{top_app['application_name']}' leads with {top_app['usage_metrics']['total_hours']} hours ({top_app['usage_metrics']['usage_percentage']}% of total usage)",
                f"Top application has {top_app['user_metrics']['unique_users']} users with {top_app['session_metrics']['avg_session_minutes']} minutes average session length",
                f"{len(high_usage_apps)} applications classified as high-usage, {len(medium_usage_apps)} as medium-usage, {len(low_usage_apps)} as low-usage"
            ])
            
            # Usage concentration analysis
            if len(applications) >= 5:
                top_5_percentage = sum(app['usage_metrics']['usage_percentage'] for app in applications[:5])
                insights["key_findings"].append(f"Top 5 applications account for {round(top_5_percentage, 1)}% of total usage time")
                
                if top_5_percentage > 80:
                    insights["recommendations"].append("High usage concentration - consider promoting underutilized applications")
                elif top_5_percentage < 50:
                    insights["recommendations"].append("Well-distributed usage pattern - good application portfolio balance")
        
        # Session pattern recommendations
        if applications:
            high_variability_apps = [app for app in applications if app['session_metrics']['session_variability'] > 30]
            if high_variability_apps:
                insights["recommendations"].append(f"Investigate {len(high_variability_apps)} applications with high session variability (>30 min std dev)")
            
            consistent_usage_apps = [app for app in applications if app['timeline']['usage_frequency'] > 50]
            if consistent_usage_apps:
                insights["recommendations"].append(f"Leverage {len(consistent_usage_apps)} applications with consistent usage patterns (>50% frequency)")
            
            power_user_apps = [app for app in applications if app['user_metrics']['avg_usage_per_user_hours'] > 10]
            if power_user_apps:
                insights["recommendations"].append(f"Focus on {len(power_user_apps)} applications with power users (>10 hours per user)")
        
        return {
            "status": "success",
            "data": {
                "tool": "usage_time_stats",
                "description": "Comprehensive usage time statistics with detailed analytics",
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit,
                    "platform": platform,
                    "min_usage_hours": min_usage_hours
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(applications),
                "applications": applications
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in usage_time_stats: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze usage time statistics: {str(e)}",
            "tool": "usage_time_stats"
        }
