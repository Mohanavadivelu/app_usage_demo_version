"""
Tool: Usage Percentage Breakdown
Category: Cross Analysis
Feature ID: 46

Description:
    Usage percentage per app per user - analyzes how users distribute their time
    across different applications, providing insights into app usage patterns and preferences.

Parameters:
    - limit (int, optional): Maximum number of user records to return (default: 100)
    - min_apps (int, optional): Minimum number of apps a user must use to be included (default: 2)
    - time_period_days (int, optional): Time period in days to analyze (default: 30)

Returns:
    - Analytics results showing usage percentage breakdown per user with detailed insights

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
async def usage_percentage_breakdown(
    limit: Optional[int] = 100,
    min_apps: Optional[int] = 2,
    time_period_days: Optional[int] = 30
) -> str:
    """
    Analyze usage percentage per app per user.
    
    Provides detailed breakdown of how users distribute their time across
    different applications, revealing usage patterns and app preferences.
    
    Args:
        limit: Maximum number of user records to return (default: 100)
        min_apps: Minimum number of apps a user must use to be included (default: 2)
        time_period_days: Time period in days to analyze (default: 30)
    
    Returns:
        JSON string containing usage percentage breakdown with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_apps is not None and (min_apps < 1 or min_apps > 50):
            raise ValueError("min_apps must be between 1 and 50")
        if time_period_days is not None and (time_period_days < 1 or time_period_days > 365):
            raise ValueError("time_period_days must be between 1 and 365")
        
        # Set defaults
        limit = limit or 100
        min_apps = min_apps or 2
        time_period_days = time_period_days or 30
        
        logger.info(f"Analyzing usage percentage breakdown with limit={limit}, min_apps={min_apps}, time_period_days={time_period_days}")
        
        # Query to calculate usage percentage breakdown per user
        query = """
        WITH user_total_usage AS (
            SELECT 
                user_id,
                SUM(duration_minutes) as total_duration_minutes,
                COUNT(DISTINCT app_name) as total_apps_used,
                COUNT(*) as total_sessions
            FROM app_usage 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY user_id
            HAVING COUNT(DISTINCT app_name) >= ?
        ),
        user_app_breakdown AS (
            SELECT 
                u.user_id,
                u.app_name,
                SUM(u.duration_minutes) as app_duration_minutes,
                COUNT(*) as app_sessions,
                ROUND(AVG(u.duration_minutes), 2) as avg_session_duration,
                MIN(u.timestamp) as first_usage,
                MAX(u.timestamp) as last_usage,
                COUNT(DISTINCT DATE(u.timestamp)) as active_days
            FROM app_usage u
            WHERE u.timestamp >= datetime('now', '-' || ? || ' days')
                AND u.user_id IN (SELECT user_id FROM user_total_usage)
            GROUP BY u.user_id, u.app_name
        ),
        percentage_analysis AS (
            SELECT 
                uab.user_id,
                uab.app_name,
                uab.app_duration_minutes,
                uab.app_sessions,
                uab.avg_session_duration,
                uab.first_usage,
                uab.last_usage,
                uab.active_days,
                utu.total_duration_minutes,
                utu.total_apps_used,
                utu.total_sessions,
                ROUND(
                    (uab.app_duration_minutes * 100.0) / utu.total_duration_minutes, 
                    2
                ) as usage_percentage,
                ROUND(
                    (uab.app_sessions * 100.0) / utu.total_sessions, 
                    2
                ) as session_percentage,
                CASE 
                    WHEN (uab.app_duration_minutes * 100.0) / utu.total_duration_minutes >= 50 THEN 'Dominant'
                    WHEN (uab.app_duration_minutes * 100.0) / utu.total_duration_minutes >= 25 THEN 'Primary'
                    WHEN (uab.app_duration_minutes * 100.0) / utu.total_duration_minutes >= 10 THEN 'Regular'
                    WHEN (uab.app_duration_minutes * 100.0) / utu.total_duration_minutes >= 5 THEN 'Occasional'
                    ELSE 'Minimal'
                END as usage_category
            FROM user_app_breakdown uab
            JOIN user_total_usage utu ON uab.user_id = utu.user_id
        ),
        user_summary AS (
            SELECT 
                user_id,
                total_duration_minutes,
                total_apps_used,
                total_sessions,
                COUNT(*) as apps_analyzed,
                MAX(usage_percentage) as max_app_percentage,
                MIN(usage_percentage) as min_app_percentage,
                ROUND(AVG(usage_percentage), 2) as avg_app_percentage,
                SUM(CASE WHEN usage_category = 'Dominant' THEN 1 ELSE 0 END) as dominant_apps,
                SUM(CASE WHEN usage_category = 'Primary' THEN 1 ELSE 0 END) as primary_apps,
                CASE 
                    WHEN MAX(usage_percentage) >= 70 THEN 'Highly Focused'
                    WHEN MAX(usage_percentage) >= 50 THEN 'Moderately Focused'
                    WHEN MAX(usage_percentage) >= 30 THEN 'Balanced'
                    ELSE 'Highly Distributed'
                END as usage_pattern
            FROM percentage_analysis
            GROUP BY user_id, total_duration_minutes, total_apps_used, total_sessions
        )
        SELECT 
            pa.user_id,
            pa.app_name,
            pa.app_duration_minutes,
            pa.app_sessions,
            pa.avg_session_duration,
            pa.first_usage,
            pa.last_usage,
            pa.active_days,
            pa.total_duration_minutes,
            pa.total_apps_used,
            pa.total_sessions,
            pa.usage_percentage,
            pa.session_percentage,
            pa.usage_category,
            us.max_app_percentage,
            us.min_app_percentage,
            us.avg_app_percentage,
            us.dominant_apps,
            us.primary_apps,
            us.usage_pattern
        FROM percentage_analysis pa
        JOIN user_summary us ON pa.user_id = us.user_id
        ORDER BY pa.user_id, pa.usage_percentage DESC
        LIMIT ?
        """
        
        params = (time_period_days, min_apps, time_period_days, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "usage_percentage_breakdown",
                "status": "success",
                "message": "No usage data found with the specified criteria",
                "data": {
                    "user_breakdowns": [],
                    "total_records": 0,
                    "parameters": {
                        "limit": limit,
                        "min_apps": min_apps,
                        "time_period_days": time_period_days
                    }
                }
            }, indent=2)
        
        # Process results and group by user
        user_breakdowns = {}
        usage_pattern_distribution = {}
        usage_category_distribution = {}
        
        for row in results:
            user_id = row[0]
            
            if user_id not in user_breakdowns:
                user_breakdowns[user_id] = {
                    "user_id": user_id,
                    "user_summary": {
                        "total_duration_minutes": row[8],
                        "total_apps_used": row[9],
                        "total_sessions": row[10],
                        "max_app_percentage": row[14],
                        "min_app_percentage": row[15],
                        "avg_app_percentage": row[16],
                        "dominant_apps": row[17],
                        "primary_apps": row[18],
                        "usage_pattern": row[19]
                    },
                    "app_breakdowns": []
                }
                
                # Update distributions
                pattern = row[19]
                usage_pattern_distribution[pattern] = usage_pattern_distribution.get(pattern, 0) + 1
            
            # Add app breakdown
            app_breakdown = {
                "app_name": row[1],
                "metrics": {
                    "duration_minutes": row[2],
                    "sessions": row[3],
                    "avg_session_duration": row[4],
                    "active_days": row[7],
                    "usage_percentage": row[11],
                    "session_percentage": row[12]
                },
                "usage_period": {
                    "first_usage": row[5],
                    "last_usage": row[6]
                },
                "classification": {
                    "usage_category": row[13]
                }
            }
            user_breakdowns[user_id]["app_breakdowns"].append(app_breakdown)
            
            # Update category distribution
            category = row[13]
            usage_category_distribution[category] = usage_category_distribution.get(category, 0) + 1
        
        # Convert to list and calculate additional statistics
        user_list = list(user_breakdowns.values())
        
        # Calculate summary statistics
        if user_list:
            total_users = len(user_list)
            avg_apps_per_user = sum(user["user_summary"]["total_apps_used"] for user in user_list) / total_users
            avg_total_duration = sum(user["user_summary"]["total_duration_minutes"] for user in user_list) / total_users
            
            # Find most focused and most distributed users
            most_focused_user = max(user_list, key=lambda x: x["user_summary"]["max_app_percentage"])
            most_distributed_user = min(user_list, key=lambda x: x["user_summary"]["max_app_percentage"])
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if user_list:
            # Usage pattern insights
            highly_focused = usage_pattern_distribution.get('Highly Focused', 0)
            balanced = usage_pattern_distribution.get('Balanced', 0)
            distributed = usage_pattern_distribution.get('Highly Distributed', 0)
            
            insights.append(f"Analyzed {total_users} users with average {round(avg_apps_per_user, 1)} apps per user")
            insights.append(f"Most focused user spends {most_focused_user['user_summary']['max_app_percentage']}% time on their primary app")
            insights.append(f"Most distributed user's primary app only accounts for {most_distributed_user['user_summary']['max_app_percentage']}% of their time")
            
            if highly_focused > 0:
                insights.append(f"{highly_focused} users are highly focused (70%+ time on primary app)")
            if balanced > 0:
                insights.append(f"{balanced} users have balanced usage patterns")
            if distributed > 0:
                insights.append(f"{distributed} users have highly distributed usage")
            
            # Category insights
            dominant_usage = usage_category_distribution.get('Dominant', 0)
            primary_usage = usage_category_distribution.get('Primary', 0)
            
            if dominant_usage > 0:
                insights.append(f"{dominant_usage} app-user combinations show dominant usage (50%+ time)")
            if primary_usage > 0:
                insights.append(f"{primary_usage} app-user combinations show primary usage (25-50% time)")
            
            # Recommendations
            if highly_focused > 0:
                recommendations.append("Focus on improving core features for highly focused users")
                recommendations.append("Consider upselling premium features for primary apps")
            
            if balanced > 0:
                recommendations.append("Develop workflow integration features for balanced users")
            
            if distributed > 0:
                recommendations.append("Create unified dashboards for users with distributed usage")
                recommendations.append("Consider cross-app synchronization features")
            
            recommendations.append("Analyze dominant app categories for market positioning")
            recommendations.append("Use usage patterns to personalize user experiences")
        
        response_data = {
            "tool": "usage_percentage_breakdown",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "user_breakdowns": user_list,
                "summary": {
                    "total_users": len(user_list),
                    "total_records": len(results),
                    "parameters_used": {
                        "limit": limit,
                        "min_apps": min_apps,
                        "time_period_days": time_period_days
                    },
                    "statistics": {
                        "avg_apps_per_user": round(avg_apps_per_user, 2) if user_list else 0,
                        "avg_total_duration_minutes": round(avg_total_duration, 2) if user_list else 0
                    },
                    "distributions": {
                        "usage_patterns": usage_pattern_distribution,
                        "usage_categories": usage_category_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed usage percentage breakdown for {len(user_list)} users")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in usage_percentage_breakdown: {e}")
        return json.dumps({
            "tool": "usage_percentage_breakdown",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze usage percentage breakdown"
        }, indent=2)
