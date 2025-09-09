"""
Tool: User App Matrix
Category: Cross Analysis
Feature ID: 47

Description:
    Cross-tab display of users vs applications matrix showing usage patterns.
    Creates a comprehensive matrix view of user-application relationships with detailed analytics.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of user-app combinations to return (default: 100)
    - min_usage_minutes (int, optional): Minimum usage minutes to include combination (default: 10)

Returns:
    - Cross-tab matrix of users vs applications with detailed analytics

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
async def user_app_matrix(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    min_usage_minutes: Optional[int] = 10
) -> str:
    """
    Generate cross-tab display of users vs applications matrix.
    
    Creates a comprehensive matrix view showing usage patterns between users
    and applications, with detailed analytics and insights.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        limit: Maximum number of user-app combinations to return (default: 100)
        min_usage_minutes: Minimum usage minutes to include combination (default: 10)
    
    Returns:
        JSON string containing user-app matrix with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_usage_minutes is not None and (min_usage_minutes < 1 or min_usage_minutes > 1440):
            raise ValueError("min_usage_minutes must be between 1 and 1440 (24 hours)")
        
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
        min_usage_minutes = min_usage_minutes or 10
        
        # Set default date range if not provided (last 30 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Generating user-app matrix from {start_date} to {end_date} with limit={limit}, min_usage_minutes={min_usage_minutes}")
        
        # Build date filter condition
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE DATE(timestamp) BETWEEN ? AND ?"
            params = [start_date, end_date]
        
        # Query to generate user-app matrix
        query = f"""
        WITH user_app_usage AS (
            SELECT 
                user_id,
                app_name,
                SUM(duration_minutes) as total_duration_minutes,
                COUNT(*) as session_count,
                MIN(timestamp) as first_usage,
                MAX(timestamp) as last_usage,
                ROUND(AVG(duration_minutes), 2) as avg_session_duration,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM app_usage
            {date_filter}
            GROUP BY user_id, app_name
            HAVING SUM(duration_minutes) >= ?
        ),
        user_totals AS (
            SELECT 
                user_id,
                SUM(total_duration_minutes) as user_total_minutes,
                COUNT(DISTINCT app_name) as total_apps_used,
                SUM(session_count) as total_sessions
            FROM user_app_usage
            GROUP BY user_id
        ),
        app_totals AS (
            SELECT 
                app_name,
                SUM(total_duration_minutes) as app_total_minutes,
                COUNT(DISTINCT user_id) as total_users,
                SUM(session_count) as total_sessions
            FROM user_app_usage
            GROUP BY app_name
        ),
        matrix_analysis AS (
            SELECT 
                uau.user_id,
                uau.app_name,
                uau.total_duration_minutes,
                uau.session_count,
                uau.first_usage,
                uau.last_usage,
                uau.avg_session_duration,
                uau.active_days,
                ut.user_total_minutes,
                ut.total_apps_used,
                ut.total_sessions as user_total_sessions,
                at.app_total_minutes,
                at.total_users as app_total_users,
                at.total_sessions as app_total_sessions,
                ROUND(
                    (uau.total_duration_minutes * 100.0) / ut.user_total_minutes, 
                    2
                ) as user_app_percentage,
                ROUND(
                    (uau.total_duration_minutes * 100.0) / at.app_total_minutes, 
                    2
                ) as app_user_percentage,
                CASE 
                    WHEN uau.total_duration_minutes >= 480 THEN 'Heavy Usage'
                    WHEN uau.total_duration_minutes >= 120 THEN 'Moderate Usage'
                    WHEN uau.total_duration_minutes >= 30 THEN 'Light Usage'
                    ELSE 'Minimal Usage'
                END as usage_intensity,
                CASE 
                    WHEN uau.active_days >= 20 THEN 'Daily User'
                    WHEN uau.active_days >= 10 THEN 'Regular User'
                    WHEN uau.active_days >= 5 THEN 'Occasional User'
                    ELSE 'Rare User'
                END as usage_frequency,
                ROUND(uau.total_duration_minutes / uau.active_days, 2) as avg_daily_minutes
            FROM user_app_usage uau
            JOIN user_totals ut ON uau.user_id = ut.user_id
            JOIN app_totals at ON uau.app_name = at.app_name
        )
        SELECT 
            user_id,
            app_name,
            total_duration_minutes,
            session_count,
            first_usage,
            last_usage,
            avg_session_duration,
            active_days,
            user_total_minutes,
            total_apps_used,
            user_total_sessions,
            app_total_minutes,
            app_total_users,
            app_total_sessions,
            user_app_percentage,
            app_user_percentage,
            usage_intensity,
            usage_frequency,
            avg_daily_minutes
        FROM matrix_analysis
        ORDER BY user_id, total_duration_minutes DESC
        LIMIT ?
        """
        
        # Add min_usage_minutes and limit to params
        params.append(min_usage_minutes)
        params.append(limit)
        
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "user_app_matrix",
                "status": "success",
                "message": "No user-app combinations found with the specified criteria",
                "data": {
                    "matrix_data": [],
                    "total_combinations": 0,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "min_usage_minutes": min_usage_minutes
                    }
                }
            }, indent=2)
        
        # Process results into matrix format
        matrix_data = []
        user_summaries = {}
        app_summaries = {}
        usage_intensity_distribution = {}
        usage_frequency_distribution = {}
        
        for row in results:
            user_id = row[0]
            app_name = row[1]
            
            # Build matrix entry
            matrix_entry = {
                "user_id": user_id,
                "app_name": app_name,
                "usage_metrics": {
                    "total_duration_minutes": row[2],
                    "session_count": row[3],
                    "avg_session_duration": row[6],
                    "active_days": row[7],
                    "avg_daily_minutes": row[18]
                },
                "usage_period": {
                    "first_usage": row[4],
                    "last_usage": row[5]
                },
                "percentage_analysis": {
                    "user_app_percentage": row[14],  # % of user's total time
                    "app_user_percentage": row[15]   # % of app's total usage
                },
                "classification": {
                    "usage_intensity": row[16],
                    "usage_frequency": row[17]
                },
                "context": {
                    "user_total_minutes": row[8],
                    "user_total_apps": row[9],
                    "user_total_sessions": row[10],
                    "app_total_minutes": row[11],
                    "app_total_users": row[12],
                    "app_total_sessions": row[13]
                }
            }
            matrix_data.append(matrix_entry)
            
            # Update user summary
            if user_id not in user_summaries:
                user_summaries[user_id] = {
                    "user_id": user_id,
                    "total_minutes": row[8],
                    "total_apps": row[9],
                    "total_sessions": row[10],
                    "apps_in_matrix": []
                }
            user_summaries[user_id]["apps_in_matrix"].append(app_name)
            
            # Update app summary
            if app_name not in app_summaries:
                app_summaries[app_name] = {
                    "app_name": app_name,
                    "total_minutes": row[11],
                    "total_users": row[12],
                    "total_sessions": row[13],
                    "users_in_matrix": []
                }
            app_summaries[app_name]["users_in_matrix"].append(user_id)
            
            # Update distributions
            intensity = row[16]
            frequency = row[17]
            usage_intensity_distribution[intensity] = usage_intensity_distribution.get(intensity, 0) + 1
            usage_frequency_distribution[frequency] = usage_frequency_distribution.get(frequency, 0) + 1
        
        # Calculate summary statistics
        total_combinations = len(matrix_data)
        unique_users = len(user_summaries)
        unique_apps = len(app_summaries)
        
        if matrix_data:
            avg_duration_per_combination = sum(entry["usage_metrics"]["total_duration_minutes"] for entry in matrix_data) / total_combinations
            avg_sessions_per_combination = sum(entry["usage_metrics"]["session_count"] for entry in matrix_data) / total_combinations
            
            # Find top combinations
            top_duration_combo = max(matrix_data, key=lambda x: x["usage_metrics"]["total_duration_minutes"])
            top_sessions_combo = max(matrix_data, key=lambda x: x["usage_metrics"]["session_count"])
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if matrix_data:
            insights.append(f"Matrix contains {total_combinations} user-app combinations across {unique_users} users and {unique_apps} apps")
            insights.append(f"Average {round(avg_duration_per_combination, 1)} minutes per user-app combination")
            insights.append(f"Top combination: User {top_duration_combo['user_id']} with {top_duration_combo['app_name']} ({top_duration_combo['usage_metrics']['total_duration_minutes']} minutes)")
            
            # Usage intensity insights
            heavy_usage = usage_intensity_distribution.get('Heavy Usage', 0)
            if heavy_usage > 0:
                insights.append(f"{heavy_usage} combinations show heavy usage (8+ hours)")
            
            # Usage frequency insights
            daily_users = usage_frequency_distribution.get('Daily User', 0)
            if daily_users > 0:
                insights.append(f"{daily_users} combinations represent daily usage patterns")
            
            # Recommendations
            if heavy_usage > 0:
                recommendations.append("Focus on retention strategies for heavy usage combinations")
                recommendations.append("Consider premium features for high-engagement user-app pairs")
            
            if daily_users > 0:
                recommendations.append("Develop habit-forming features for daily usage patterns")
            
            recommendations.append("Use matrix data to identify cross-selling opportunities")
            recommendations.append("Analyze user-app clusters for personalized recommendations")
            recommendations.append("Monitor matrix changes over time for trend analysis")
        
        response_data = {
            "tool": "user_app_matrix",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "matrix_data": matrix_data,
                "summary": {
                    "total_combinations": total_combinations,
                    "unique_users": unique_users,
                    "unique_apps": unique_apps,
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "limit": limit,
                        "min_usage_minutes": min_usage_minutes
                    },
                    "statistics": {
                        "avg_duration_per_combination": round(avg_duration_per_combination, 2) if matrix_data else 0,
                        "avg_sessions_per_combination": round(avg_sessions_per_combination, 2) if matrix_data else 0
                    },
                    "distributions": {
                        "usage_intensity": usage_intensity_distribution,
                        "usage_frequency": usage_frequency_distribution
                    }
                },
                "user_summaries": list(user_summaries.values()),
                "app_summaries": list(app_summaries.values()),
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully generated user-app matrix with {total_combinations} combinations")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in user_app_matrix: {e}")
        return json.dumps({
            "tool": "user_app_matrix",
            "status": "error",
            "error": str(e),
            "message": "Failed to generate user-app matrix"
        }, indent=2)
