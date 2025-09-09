"""
Tool: User Last App
Category: User Centric
Feature ID: 69

Description:
    Comprehensive analysis of the last application used by a specific user

Parameters:
    - user (str, required): User identifier to analyze
    - include_context (bool, optional): Include contextual information about the application (default: True)

Returns:
    - Comprehensive analysis of user's last application usage with detailed analytics and insights

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

logger = logging.getLogger(__name__)


@mcp.tool()
async def user_last_app(
    user: str,
    include_context: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Comprehensive analysis of the last application used by a specific user.
    
    Provides detailed insights into user's most recent application usage, including:
    - Last application used and session details
    - Historical usage patterns for that application
    - Comparative analysis with user's other applications
    - Usage trends and patterns
    - Contextual recommendations
    
    Args:
        user: User identifier to analyze (required)
        include_context: Include contextual information about the application (default: True)
    
    Returns:
        Dict containing comprehensive last application usage analysis with insights
    """
    try:
        # Parameter validation
        if not user or not isinstance(user, str):
            return {
                "status": "error",
                "message": "user is required and must be a non-empty string"
            }
        
        # Set defaults
        include_context = include_context if include_context is not None else True
        
        # Build query to find the last application used
        query = """
        SELECT 
            user,
            application_name,
            platform,
            log_date,
            duration_seconds
        FROM app_usage
        WHERE user = ?
        ORDER BY log_date DESC, duration_seconds DESC
        LIMIT 1
        """
        
        # Execute main query
        with get_database_connection() as conn:
            cursor = conn.cursor()
            start_time = datetime.now()
            cursor.execute(query, [user])
            result = cursor.fetchone()
            
            if not result:
                return {
                    "status": "success",
                    "data": {
                        "tool": "user_last_app",
                        "description": f"Last application analysis for user '{user}'",
                        "user": user,
                        "query_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                        "user_found": False
                    },
                    "insights": {
                        "summary": f"No application usage data found for user '{user}'",
                        "recommendations": [
                            "Verify the user identifier spelling",
                            "Check if the user has any recorded activity in the system",
                            "Consider if this is a new user who hasn't started using applications yet"
                        ]
                    }
                }
            
            # Process main results
            last_app_name = result[1]
            last_platform = result[2]
            last_usage_date = result[3]
            last_session_duration = result[4]
            
            # Calculate days since last use
            days_since_last_use = (datetime.now().date() - datetime.strptime(last_usage_date, '%Y-%m-%d').date()).days
            
            # Get contextual information if requested
            app_context = {}
            user_app_history = {}
            comparative_data = {}
            
            if include_context:
                # Get detailed statistics for the last application used by this user
                app_stats_query = """
                SELECT 
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
                WHERE user = ? AND application_name = ?
                """
                
                cursor.execute(app_stats_query, [user, last_app_name])
                app_stats = cursor.fetchone()
                
                if app_stats:
                    usage_span_days = (datetime.strptime(app_stats[6], '%Y-%m-%d') - 
                                     datetime.strptime(app_stats[5], '%Y-%m-%d')).days + 1
                    
                    user_app_history = {
                        "total_sessions": int(app_stats[0]),
                        "total_hours": round(app_stats[1] / 3600, 2),
                        "avg_session_minutes": round(app_stats[2] / 60, 2),
                        "min_session_minutes": round(app_stats[3] / 60, 2),
                        "max_session_minutes": round(app_stats[4] / 60, 2),
                        "first_usage_date": app_stats[5],
                        "last_usage_date": app_stats[6],
                        "active_days": int(app_stats[7]),
                        "platforms_used": int(app_stats[8]),
                        "usage_span_days": usage_span_days,
                        "usage_frequency": round((app_stats[7] / usage_span_days) * 100, 1) if usage_span_days > 0 else 0
                    }
                
                # Get user's overall application usage for comparison
                user_total_query = """
                SELECT 
                    COUNT(DISTINCT application_name) as total_apps,
                    SUM(duration_seconds) as total_seconds,
                    COUNT(*) as total_sessions
                FROM app_usage
                WHERE user = ?
                """
                
                cursor.execute(user_total_query, [user])
                user_totals = cursor.fetchone()
                
                if user_totals and app_stats:
                    comparative_data = {
                        "app_percentage_of_total_usage": round((app_stats[1] / user_totals[1]) * 100, 2) if user_totals[1] > 0 else 0,
                        "app_percentage_of_total_sessions": round((app_stats[0] / user_totals[2]) * 100, 2) if user_totals[2] > 0 else 0,
                        "user_total_apps": int(user_totals[0]),
                        "app_rank_by_usage": None  # Will be calculated below
                    }
                    
                    # Get app ranking
                    ranking_query = """
                    SELECT COUNT(*) + 1 as app_rank
                    FROM (
                        SELECT application_name, SUM(duration_seconds) as total_seconds
                        FROM app_usage
                        WHERE user = ?
                        GROUP BY application_name
                        HAVING SUM(duration_seconds) > ?
                    )
                    """
                    
                    cursor.execute(ranking_query, [user, app_stats[1]])
                    rank_result = cursor.fetchone()
                    if rank_result:
                        comparative_data["app_rank_by_usage"] = int(rank_result[0])
                
                # Get recent usage pattern for this application
                recent_usage_query = """
                SELECT 
                    log_date,
                    duration_seconds,
                    platform
                FROM app_usage
                WHERE user = ? AND application_name = ?
                ORDER BY log_date DESC
                LIMIT 5
                """
                
                cursor.execute(recent_usage_query, [user, last_app_name])
                recent_usage_results = cursor.fetchall()
                
                recent_sessions = []
                for row in recent_usage_results:
                    session_data = {
                        "date": row[0],
                        "duration_minutes": round(row[1] / 60, 2),
                        "platform": row[2],
                        "days_ago": (datetime.now().date() - datetime.strptime(row[0], '%Y-%m-%d').date()).days
                    }
                    recent_sessions.append(session_data)
                
                app_context = {
                    "recent_sessions": recent_sessions
                }
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate insights
        last_session_minutes = round(last_session_duration / 60, 2)
        
        # Determine recency status
        if days_since_last_use == 0:
            recency_status = "Used Today"
        elif days_since_last_use == 1:
            recency_status = "Used Yesterday"
        elif days_since_last_use <= 7:
            recency_status = "Used This Week"
        elif days_since_last_use <= 30:
            recency_status = "Used This Month"
        else:
            recency_status = "Used Long Ago"
        
        # Application importance classification
        if include_context and comparative_data:
            usage_percentage = comparative_data.get("app_percentage_of_total_usage", 0)
            if usage_percentage > 30:
                app_importance = "Primary Application"
            elif usage_percentage > 15:
                app_importance = "Secondary Application"
            elif usage_percentage > 5:
                app_importance = "Regular Application"
            else:
                app_importance = "Occasional Application"
        else:
            app_importance = "Unknown"
        
        insights = {
            "summary": f"User '{user}' last used '{last_app_name}' on {last_usage_date} ({days_since_last_use} days ago)",
            "key_findings": [
                f"Last application: {last_app_name} on {last_platform}",
                f"Last session duration: {last_session_minutes} minutes",
                f"Recency: {recency_status}",
                f"Application importance: {app_importance}"
            ],
            "recommendations": []
        }
        
        # Add contextual findings if available
        if include_context and user_app_history:
            insights["key_findings"].extend([
                f"User has {user_app_history['total_sessions']} total sessions with this app ({user_app_history['total_hours']} hours)",
                f"Average session length: {user_app_history['avg_session_minutes']} minutes",
                f"Usage frequency: {user_app_history['usage_frequency']}% over {user_app_history['usage_span_days']} days"
            ])
        
        # Generate recommendations based on usage patterns
        if recency_status == "Used Today":
            insights["recommendations"].extend([
                "User is actively using this application - ensure optimal performance",
                "Consider providing advanced features or tips for this application"
            ])
        elif recency_status in ["Used Yesterday", "Used This Week"]:
            insights["recommendations"].extend([
                "User recently used this application - maintain engagement",
                "Monitor for any performance issues or feature requests"
            ])
        elif recency_status == "Used This Month":
            insights["recommendations"].extend([
                "User hasn't used this application recently - consider re-engagement",
                "Send updates or new feature announcements for this application"
            ])
        else:  # Used Long Ago
            insights["recommendations"].extend([
                "User hasn't used this application in a while - investigate reasons",
                "Consider win-back campaigns or check for technical issues"
            ])
        
        # Additional recommendations based on context
        if include_context and comparative_data:
            if app_importance == "Primary Application":
                insights["recommendations"].append("This is a primary application - prioritize support and feature development")
            elif app_importance == "Occasional Application":
                insights["recommendations"].append("This is an occasional-use application - consider usage barriers or training needs")
        
        if include_context and user_app_history and user_app_history.get("platforms_used", 0) > 1:
            insights["recommendations"].append("User uses this application across multiple platforms - ensure cross-platform consistency")
        
        # Build response data
        response_data = {
            "tool": "user_last_app",
            "description": f"Last application analysis for user '{user}'",
            "user": user,
            "parameters": {
                "include_context": include_context
            },
            "query_time_ms": round(query_time, 2),
            "user_found": True,
            "last_application": {
                "application_name": last_app_name,
                "platform": last_platform,
                "usage_date": last_usage_date,
                "session_duration_minutes": last_session_minutes,
                "days_since_last_use": days_since_last_use,
                "recency_status": recency_status,
                "app_importance": app_importance
            }
        }
        
        # Add contextual information if requested
        if include_context:
            if user_app_history:
                response_data["application_history"] = user_app_history
            if comparative_data:
                response_data["comparative_analysis"] = comparative_data
            if app_context:
                response_data["application_context"] = app_context
        
        return {
            "status": "success",
            "data": response_data,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in user_last_app: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze last application for user '{user}': {str(e)}",
            "tool": "user_last_app"
        }
