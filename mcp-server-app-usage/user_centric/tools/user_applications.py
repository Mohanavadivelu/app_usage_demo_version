"""
Tool: User Applications
Category: User Centric
Feature ID: 67

Description:
    Comprehensive analysis of all applications used by a specific user

Parameters:
    - user (str, required): User identifier to analyze
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of applications to return (default: 100, max: 1000)
    - platform (str, optional): Platform to filter by

Returns:
    - Comprehensive analysis of user's application portfolio with detailed analytics and insights

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
async def user_applications(
    user: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive analysis of all applications used by a specific user.
    
    Provides detailed insights into user's application portfolio and usage patterns, including:
    - Complete application inventory for the user
    - Usage time and session statistics per application
    - Application preference rankings
    - Platform distribution analysis
    - Usage diversity and concentration metrics
    - Temporal usage patterns and trends
    
    Args:
        user: User identifier to analyze (required)
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        limit: Maximum number of applications to return (1-1000, default: 100)
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
    
    Returns:
        Dict containing comprehensive user application portfolio analysis with insights
    """
    try:
        # Parameter validation
        if not user or not isinstance(user, str):
            return {
                "status": "error",
                "message": "user is required and must be a non-empty string"
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
        
        query += """
            GROUP BY application_name, platform
        ),
        aggregated_app_stats AS (
            SELECT 
                application_name,
                SUM(total_seconds) as total_seconds,
                SUM(total_sessions) as total_sessions,
                AVG(avg_session_seconds) as avg_session_seconds,
                MIN(min_session_seconds) as min_session_seconds,
                MAX(max_session_seconds) as max_session_seconds,
                AVG(stddev_session_seconds) as avg_stddev_session_seconds,
                MIN(first_usage_date) as first_usage_date,
                MAX(last_usage_date) as last_usage_date,
                SUM(active_days) as total_active_days,
                MAX(platforms_used) as platforms_used
            FROM user_app_stats
            GROUP BY application_name
        ),
        user_totals AS (
            SELECT 
                SUM(total_seconds) as grand_total_seconds,
                SUM(total_sessions) as grand_total_sessions,
                COUNT(*) as total_applications,
                AVG(total_seconds) as avg_app_usage_seconds,
                STDDEV(total_seconds) as stddev_app_usage_seconds,
                MIN(first_usage_date) as user_first_usage,
                MAX(last_usage_date) as user_last_usage
            FROM aggregated_app_stats
        ),
        app_analysis AS (
            SELECT 
                aas.*,
                ut.grand_total_seconds,
                ut.grand_total_sessions,
                ut.total_applications,
                ut.avg_app_usage_seconds,
                ut.stddev_app_usage_seconds,
                ut.user_first_usage,
                ut.user_last_usage,
                ROUND((aas.total_seconds * 100.0 / ut.grand_total_seconds), 2) as usage_percentage,
                ROUND((aas.total_sessions * 100.0 / ut.grand_total_sessions), 2) as session_percentage,
                ROW_NUMBER() OVER (ORDER BY aas.total_seconds DESC) as usage_rank,
                ROW_NUMBER() OVER (ORDER BY aas.total_sessions DESC) as session_rank,
                NTILE(4) OVER (ORDER BY aas.total_seconds) as usage_quartile,
                CASE 
                    WHEN aas.total_seconds > ut.avg_app_usage_seconds + ut.stddev_app_usage_seconds THEN 'Primary'
                    WHEN aas.total_seconds > ut.avg_app_usage_seconds THEN 'Secondary'
                    WHEN aas.total_seconds > ut.avg_app_usage_seconds - ut.stddev_app_usage_seconds THEN 'Occasional'
                    ELSE 'Rare'
                END as app_category,
                CASE 
                    WHEN aas.total_sessions >= 50 THEN 'Very High'
                    WHEN aas.total_sessions >= 20 THEN 'High'
                    WHEN aas.total_sessions >= 10 THEN 'Medium'
                    WHEN aas.total_sessions >= 5 THEN 'Low'
                    ELSE 'Very Low'
                END as usage_frequency
            FROM aggregated_app_stats aas
            CROSS JOIN user_totals ut
        )
        SELECT 
            application_name,
            total_seconds,
            total_sessions,
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
            app_category,
            usage_frequency,
            grand_total_seconds,
            grand_total_sessions,
            total_applications,
            avg_app_usage_seconds,
            stddev_app_usage_seconds,
            user_first_usage,
            user_last_usage
        FROM app_analysis
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
                    "tool": "user_applications",
                    "description": f"Applications used by user '{user}'",
                    "user": user,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "platform": platform
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "applications": []
                },
                "insights": {
                    "summary": f"No applications found for user '{user}' matching the specified criteria",
                    "recommendations": [
                        "Verify the user identifier spelling",
                        "Try expanding the date range for analysis",
                        "Check if the specified platform has recorded usage data"
                    ]
                }
            }
        
        # Process results
        applications = []
        grand_total_seconds = results[0][18] if results else 0
        grand_total_sessions = results[0][19] if results else 0
        total_applications = results[0][20] if results else 0
        avg_app_usage_seconds = results[0][21] if results else 0
        stddev_app_usage_seconds = results[0][22] if results else 0
        user_first_usage = results[0][23] if results else None
        user_last_usage = results[0][24] if results else None
        
        for row in results:
            # Calculate additional metrics
            usage_span_days = (datetime.strptime(row[8], '%Y-%m-%d') - 
                             datetime.strptime(row[7], '%Y-%m-%d')).days + 1
            usage_frequency = round((row[9] / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
            sessions_per_day = round(row[2] / row[9], 2) if row[9] > 0 else 0
            days_since_last_use = (datetime.now().date() - datetime.strptime(row[8], '%Y-%m-%d').date()).days
            
            app_data = {
                "rank": int(row[13]),  # usage_rank
                "application_name": row[0],
                "usage_metrics": {
                    "total_hours": round(row[1] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[1] / 60, 2),  # total_seconds to minutes
                    "usage_percentage": row[11],  # usage_percentage
                    "usage_quartile": int(row[15]),  # usage_quartile (1=lowest, 4=highest)
                    "app_category": row[16],  # app_category
                    "vs_average_usage": round(((row[1] - avg_app_usage_seconds) / avg_app_usage_seconds) * 100, 1) if avg_app_usage_seconds > 0 else 0
                },
                "session_metrics": {
                    "total_sessions": int(row[2]),
                    "session_percentage": row[12],  # session_percentage
                    "session_rank": int(row[14]),  # session_rank
                    "usage_frequency": row[17],  # usage_frequency
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
                    "days_since_last_use": days_since_last_use,
                    "recency_status": "Recent" if days_since_last_use <= 7 else "Moderate" if days_since_last_use <= 30 else "Stale"
                }
            }
            applications.append(app_data)
        
        # Generate insights
        total_usage_hours = round(grand_total_seconds / 3600, 2)
        user_span_days = (datetime.strptime(user_last_usage, '%Y-%m-%d') - 
                         datetime.strptime(user_first_usage, '%Y-%m-%d')).days + 1 if user_first_usage and user_last_usage else 0
        
        # Application category analysis
        primary_apps = [app for app in applications if app['usage_metrics']['app_category'] == 'Primary']
        secondary_apps = [app for app in applications if app['usage_metrics']['app_category'] == 'Secondary']
        occasional_apps = [app for app in applications if app['usage_metrics']['app_category'] == 'Occasional']
        rare_apps = [app for app in applications if app['usage_metrics']['app_category'] == 'Rare']
        
        # Usage frequency analysis
        very_high_freq = [app for app in applications if app['session_metrics']['usage_frequency'] == 'Very High']
        high_freq = [app for app in applications if app['session_metrics']['usage_frequency'] == 'High']
        medium_freq = [app for app in applications if app['session_metrics']['usage_frequency'] == 'Medium']
        low_freq = [app for app in applications if app['session_metrics']['usage_frequency'] == 'Low']
        very_low_freq = [app for app in applications if app['session_metrics']['usage_frequency'] == 'Very Low']
        
        # Recency analysis
        recent_apps = [app for app in applications if app['timeline']['recency_status'] == 'Recent']
        moderate_apps = [app for app in applications if app['timeline']['recency_status'] == 'Moderate']
        stale_apps = [app for app in applications if app['timeline']['recency_status'] == 'Stale']
        
        insights = {
            "summary": f"User '{user}' has used {len(applications)} applications with {total_usage_hours} total hours",
            "key_findings": [],
            "application_portfolio": {
                "total_applications_analyzed": len(applications),
                "total_applications_for_user": total_applications,
                "total_usage_hours": total_usage_hours,
                "total_sessions": grand_total_sessions,
                "average_usage_per_app_hours": round(avg_app_usage_seconds / 3600, 2),
                "user_activity_span_days": user_span_days,
                "app_categories": {
                    "primary": len(primary_apps),
                    "secondary": len(secondary_apps),
                    "occasional": len(occasional_apps),
                    "rare": len(rare_apps)
                },
                "usage_frequencies": {
                    "very_high": len(very_high_freq),
                    "high": len(high_freq),
                    "medium": len(medium_freq),
                    "low": len(low_freq),
                    "very_low": len(very_low_freq)
                },
                "recency_distribution": {
                    "recent": len(recent_apps),
                    "moderate": len(moderate_apps),
                    "stale": len(stale_apps)
                }
            },
            "recommendations": []
        }
        
        if applications:
            top_app = applications[0]
            insights["key_findings"].extend([
                f"Primary application: '{top_app['application_name']}' with {top_app['usage_metrics']['total_hours']} hours ({top_app['usage_metrics']['usage_percentage']}% of total usage)",
                f"Application diversity: {len(primary_apps)} primary, {len(secondary_apps)} secondary, {len(occasional_apps)} occasional, {len(rare_apps)} rare applications",
                f"Usage distribution: Top 3 applications account for {round(sum(app['usage_metrics']['usage_percentage'] for app in applications[:3]), 1)}% of total usage"
            ])
            
            # Usage concentration analysis
            if len(applications) >= 3:
                top_3_percentage = sum(app['usage_metrics']['usage_percentage'] for app in applications[:3])
                if top_3_percentage > 80:
                    insights["key_findings"].append("High usage concentration - user focuses on few applications")
                    insights["recommendations"].append("Consider workflow optimization for primary applications")
                elif top_3_percentage < 50:
                    insights["key_findings"].append("Diverse application usage - user has varied workflow")
                    insights["recommendations"].append("Analyze application switching patterns for efficiency gains")
        
        # Portfolio recommendations
        if primary_apps:
            insights["recommendations"].append(f"Optimize workflows for {len(primary_apps)} primary applications")
        
        if stale_apps:
            insights["recommendations"].append(f"Review {len(stale_apps)} stale applications for potential cleanup or re-engagement")
        
        # Platform diversity recommendations
        cross_platform_apps = [app for app in applications if app['platform_metrics']['cross_platform']]
        if cross_platform_apps:
            insights["recommendations"].append(f"Leverage {len(cross_platform_apps)} cross-platform applications for seamless workflows")
        
        # Usage pattern recommendations
        if len(very_high_freq) + len(high_freq) > len(applications) * 0.3:
            insights["recommendations"].append("Strong application engagement - consider advanced features and integrations")
        elif len(low_freq) + len(very_low_freq) > len(applications) * 0.5:
            insights["recommendations"].append("Many low-frequency applications - consider consolidation or training")
        
        return {
            "status": "success",
            "data": {
                "tool": "user_applications",
                "description": f"Comprehensive analysis of applications used by user '{user}'",
                "user": user,
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit,
                    "platform": platform
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(applications),
                "applications": applications
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_applications: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze applications for user '{user}': {str(e)}",
            "tool": "user_applications"
        }
