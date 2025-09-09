"""
Tool: Platform Usage Stats
Category: Usage Stats
Feature ID: 59

Description:
    Applications used most on each platform - analyzes platform-specific usage patterns
    to identify the most popular applications on different platforms and cross-platform trends.

Parameters:
    - platform (str, optional): Specific platform to analyze (optional)
    - limit (int, optional): Maximum number of results per platform (default: 100)
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - min_usage_minutes (int, optional): Minimum usage minutes to include app (default: 30)

Returns:
    - Applications used most on each platform with detailed analytics

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from shared.database_utils import execute_analytics_query, validate_parameters
from server_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def platform_usage_stats(
    platform: Optional[str] = None,
    limit: Optional[int] = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_usage_minutes: Optional[int] = 30
) -> str:
    """
    Analyze applications used most on each platform.
    
    Analyzes platform-specific usage patterns to identify the most popular
    applications on different platforms and cross-platform usage trends.
    
    Args:
        platform: Specific platform to analyze (optional)
        limit: Maximum number of results per platform (default: 100)
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        min_usage_minutes: Minimum usage minutes to include app (default: 30)
    
    Returns:
        JSON string containing platform usage statistics with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_usage_minutes is not None and (min_usage_minutes < 1 or min_usage_minutes > 1440):
            raise ValueError("min_usage_minutes must be between 1 and 1440")
        
        # Validate date formats
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("start_date must be in YYYY-MM-DD format")
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("end_date must be in YYYY-MM-DD format")
        
        # Set defaults
        limit = limit or 100
        min_usage_minutes = min_usage_minutes or 30
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing platform usage stats from {start_date} to {end_date} for {platform or 'all platforms'}")
        
        # Build platform filter
        platform_filter = ""
        params = [start_date, end_date, min_usage_minutes]
        if platform:
            platform_filter = "AND platform = ?"
            params.insert(2, platform)
        
        # Query to analyze platform usage statistics
        query = f"""
        WITH platform_app_stats AS (
            SELECT 
                COALESCE(platform, 'Unknown') as platform,
                app_name,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_duration_minutes,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                MIN(timestamp) as first_usage,
                MAX(timestamp) as last_usage,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            {platform_filter}
            GROUP BY COALESCE(platform, 'Unknown'), app_name
            HAVING SUM(duration_minutes) >= ?
        ),
        platform_totals AS (
            SELECT 
                platform,
                SUM(unique_users) as platform_total_users,
                SUM(total_sessions) as platform_total_sessions,
                SUM(total_duration_minutes) as platform_total_duration,
                COUNT(*) as platform_app_count
            FROM platform_app_stats
            GROUP BY platform
        ),
        ranked_platform_apps AS (
            SELECT 
                pas.*,
                pt.platform_total_users,
                pt.platform_total_sessions,
                pt.platform_total_duration,
                pt.platform_app_count,
                RANK() OVER (PARTITION BY pas.platform ORDER BY pas.total_duration_minutes DESC) as duration_rank,
                RANK() OVER (PARTITION BY pas.platform ORDER BY pas.unique_users DESC) as user_rank,
                RANK() OVER (PARTITION BY pas.platform ORDER BY pas.total_sessions DESC) as session_rank,
                ROUND((pas.total_duration_minutes * 100.0) / pt.platform_total_duration, 2) as platform_usage_percentage,
                ROUND((pas.unique_users * 100.0) / pt.platform_total_users, 2) as platform_user_percentage,
                CASE 
                    WHEN pas.total_duration_minutes >= pt.platform_total_duration * 0.2 THEN 'Dominant'
                    WHEN pas.total_duration_minutes >= pt.platform_total_duration * 0.1 THEN 'Major'
                    WHEN pas.total_duration_minutes >= pt.platform_total_duration * 0.05 THEN 'Significant'
                    WHEN pas.total_duration_minutes >= pt.platform_total_duration * 0.02 THEN 'Moderate'
                    ELSE 'Minor'
                END as platform_importance,
                ROUND(pas.total_duration_minutes / pas.unique_users, 2) as avg_duration_per_user,
                ROUND(pas.total_sessions * 1.0 / pas.unique_users, 2) as avg_sessions_per_user
            FROM platform_app_stats pas
            JOIN platform_totals pt ON pas.platform = pt.platform
        )
        SELECT 
            platform,
            app_name,
            unique_users,
            total_sessions,
            total_duration_minutes,
            avg_session_duration,
            first_usage,
            last_usage,
            active_days,
            platform_total_users,
            platform_total_sessions,
            platform_total_duration,
            platform_app_count,
            duration_rank,
            user_rank,
            session_rank,
            platform_usage_percentage,
            platform_user_percentage,
            platform_importance,
            avg_duration_per_user,
            avg_sessions_per_user
        FROM ranked_platform_apps
        WHERE duration_rank <= ?
        ORDER BY platform, duration_rank
        """
        
        params.append(limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "platform_usage_stats",
                "status": "success",
                "message": "No platform usage data found with the specified criteria",
                "data": {
                    "platform_stats": [],
                    "total_records": 0,
                    "parameters": {
                        "platform": platform,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "min_usage_minutes": min_usage_minutes
                    }
                }
            }, indent=2)
        
        # Process results and group by platform
        platform_stats = {}
        platform_importance_distribution = {}
        
        for row in results:
            platform_name = row[0]
            
            if platform_name not in platform_stats:
                platform_stats[platform_name] = {
                    "platform": platform_name,
                    "platform_summary": {
                        "total_users": row[9],
                        "total_sessions": row[10],
                        "total_duration_minutes": row[11],
                        "total_apps": row[12]
                    },
                    "top_applications": []
                }
            
            app_data = {
                "app_name": row[1],
                "usage_metrics": {
                    "unique_users": row[2],
                    "total_sessions": row[3],
                    "total_duration_minutes": row[4],
                    "avg_session_duration": row[5],
                    "active_days": row[8],
                    "avg_duration_per_user": row[19],
                    "avg_sessions_per_user": row[20]
                },
                "usage_period": {
                    "first_usage": row[6],
                    "last_usage": row[7]
                },
                "platform_analysis": {
                    "platform_usage_percentage": row[16],
                    "platform_user_percentage": row[17],
                    "platform_importance": row[18]
                },
                "rankings": {
                    "duration_rank": row[13],
                    "user_rank": row[14],
                    "session_rank": row[15]
                }
            }
            platform_stats[platform_name]["top_applications"].append(app_data)
            
            # Update importance distribution
            importance = row[18]
            platform_importance_distribution[importance] = platform_importance_distribution.get(importance, 0) + 1
        
        # Convert to list and calculate cross-platform statistics
        platform_list = list(platform_stats.values())
        
        # Calculate summary statistics
        if platform_list:
            total_platforms = len(platform_list)
            total_apps_analyzed = sum(len(p["top_applications"]) for p in platform_list)
            
            # Find platform with most usage
            most_active_platform = max(platform_list, key=lambda x: x["platform_summary"]["total_duration_minutes"])
            
            # Find most popular app across all platforms
            all_apps = []
            for platform_data in platform_list:
                for app in platform_data["top_applications"]:
                    all_apps.append((app["app_name"], app["usage_metrics"]["total_duration_minutes"], platform_data["platform"]))
            
            if all_apps:
                most_popular_app = max(all_apps, key=lambda x: x[1])
            
            # Cross-platform app analysis
            app_platform_count = {}
            for platform_data in platform_list:
                for app in platform_data["top_applications"]:
                    app_name = app["app_name"]
                    app_platform_count[app_name] = app_platform_count.get(app_name, 0) + 1
            
            cross_platform_apps = {app: count for app, count in app_platform_count.items() if count > 1}
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if platform_list:
            insights.append(f"Analyzed {total_platforms} platforms with {total_apps_analyzed} app-platform combinations")
            insights.append(f"Most active platform: {most_active_platform['platform']} with {most_active_platform['platform_summary']['total_duration_minutes']} total minutes")
            
            if all_apps:
                insights.append(f"Most popular app overall: {most_popular_app[0]} on {most_popular_app[2]} ({most_popular_app[1]} minutes)")
            
            if cross_platform_apps:
                insights.append(f"Found {len(cross_platform_apps)} apps used across multiple platforms")
                top_cross_platform = max(cross_platform_apps.items(), key=lambda x: x[1])
                insights.append(f"Most cross-platform app: {top_cross_platform[0]} (on {top_cross_platform[1]} platforms)")
            
            # Platform-specific insights
            for platform_data in platform_list:
                platform_name = platform_data["platform"]
                top_app = platform_data["top_applications"][0] if platform_data["top_applications"] else None
                if top_app:
                    insights.append(f"{platform_name} top app: {top_app['app_name']} ({top_app['platform_analysis']['platform_usage_percentage']}% of platform usage)")
            
            # Importance distribution insights
            dominant_apps = platform_importance_distribution.get('Dominant', 0)
            major_apps = platform_importance_distribution.get('Major', 0)
            
            if dominant_apps > 0:
                insights.append(f"{dominant_apps} apps are dominant on their platforms (20%+ usage)")
            if major_apps > 0:
                insights.append(f"{major_apps} apps are major on their platforms (10-20% usage)")
            
            # Recommendations
            if cross_platform_apps:
                recommendations.append("Focus on cross-platform apps for unified user experience")
                recommendations.append("Consider cross-platform feature parity for popular apps")
            
            if dominant_apps > 0:
                recommendations.append("Prioritize platform-specific optimizations for dominant apps")
                recommendations.append("Leverage dominant apps for platform-specific marketing")
            
            # Platform-specific recommendations
            for platform_data in platform_list:
                platform_name = platform_data["platform"]
                if platform_data["platform_summary"]["total_apps"] < 5:
                    recommendations.append(f"Consider expanding app portfolio for {platform_name}")
                elif platform_data["platform_summary"]["total_apps"] > 20:
                    recommendations.append(f"Focus on top-performing apps for {platform_name}")
            
            recommendations.append("Use platform usage data for targeted development and marketing")
            recommendations.append("Monitor platform trends for strategic platform decisions")
            recommendations.append("Consider platform-specific user behavior in app design")
        
        response_data = {
            "tool": "platform_usage_stats",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "platform_stats": platform_list,
                "summary": {
                    "total_platforms": len(platform_list),
                    "total_apps_analyzed": total_apps_analyzed if platform_list else 0,
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "platform": platform,
                        "limit": limit,
                        "min_usage_minutes": min_usage_minutes
                    },
                    "cross_platform_analysis": {
                        "cross_platform_apps_count": len(cross_platform_apps) if platform_list else 0,
                        "cross_platform_apps": list(cross_platform_apps.keys()) if platform_list else []
                    },
                    "distributions": {
                        "platform_importance": platform_importance_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed platform usage stats for {len(platform_list)} platforms")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in platform_usage_stats: {e}")
        return json.dumps({
            "tool": "platform_usage_stats",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze platform usage statistics"
        }, indent=2)
