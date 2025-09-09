"""
Tool: Common App Combinations
Category: Cross Analysis
Feature ID: 44

Description:
    Applications commonly used together - identifies app pairs and combinations
    that are frequently used by the same users within similar time periods.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - min_users (int, optional): Minimum number of users for combination to be included (default: 5)
    - time_window_hours (int, optional): Time window in hours to consider apps as used together (default: 24)

Returns:
    - Analytics results showing common app combinations with usage statistics

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
async def common_app_combinations(
    limit: Optional[int] = 100,
    min_users: Optional[int] = 5,
    time_window_hours: Optional[int] = 24
) -> str:
    """
    Identify applications commonly used together.
    
    Analyzes usage patterns to find app combinations that are frequently
    used by the same users within specified time windows.
    
    Args:
        limit: Maximum number of combinations to return (default: 100)
        min_users: Minimum number of users for combination to be included (default: 5)
        time_window_hours: Time window in hours to consider apps as used together (default: 24)
    
    Returns:
        JSON string containing common app combinations with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_users is not None and (min_users < 1 or min_users > 100):
            raise ValueError("min_users must be between 1 and 100")
        if time_window_hours is not None and (time_window_hours < 1 or time_window_hours > 168):
            raise ValueError("time_window_hours must be between 1 and 168 (1 week)")
        
        # Set defaults
        limit = limit or 100
        min_users = min_users or 5
        time_window_hours = time_window_hours or 24
        
        logger.info(f"Analyzing common app combinations with limit={limit}, min_users={min_users}, time_window_hours={time_window_hours}")
        
        # Query to find common app combinations
        query = """
        WITH user_app_sessions AS (
            -- Get user sessions with app usage within time windows
            SELECT DISTINCT
                u.user_id,
                u.app_name as app1,
                u2.app_name as app2,
                DATE(u.timestamp) as usage_date
            FROM app_usage u
            JOIN app_usage u2 ON u.user_id = u2.user_id
                AND u.app_name < u2.app_name  -- Avoid duplicates and self-pairs
                AND ABS(
                    (julianday(u2.timestamp) - julianday(u.timestamp)) * 24
                ) <= ?  -- Within time window
            WHERE u.timestamp >= datetime('now', '-90 days')  -- Last 90 days
        ),
        combination_stats AS (
            SELECT 
                app1,
                app2,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_occurrences,
                COUNT(DISTINCT usage_date) as days_observed,
                ROUND(
                    COUNT(DISTINCT user_id) * 100.0 / 
                    (SELECT COUNT(DISTINCT user_id) FROM app_usage WHERE timestamp >= datetime('now', '-90 days')),
                    2
                ) as user_percentage
            FROM user_app_sessions
            GROUP BY app1, app2
            HAVING COUNT(DISTINCT user_id) >= ?
        ),
        app_individual_stats AS (
            SELECT 
                app_name,
                COUNT(DISTINCT user_id) as individual_users
            FROM app_usage 
            WHERE timestamp >= datetime('now', '-90 days')
            GROUP BY app_name
        ),
        combination_analysis AS (
            SELECT 
                cs.*,
                a1.individual_users as app1_individual_users,
                a2.individual_users as app2_individual_users,
                ROUND(
                    cs.unique_users * 100.0 / LEAST(a1.individual_users, a2.individual_users),
                    2
                ) as combination_strength,
                ROUND(cs.total_occurrences * 1.0 / cs.unique_users, 2) as avg_occurrences_per_user,
                CASE 
                    WHEN cs.unique_users >= 50 THEN 'Very Popular'
                    WHEN cs.unique_users >= 20 THEN 'Popular'
                    WHEN cs.unique_users >= 10 THEN 'Moderate'
                    ELSE 'Emerging'
                END as popularity_tier
            FROM combination_stats cs
            JOIN app_individual_stats a1 ON cs.app1 = a1.app_name
            JOIN app_individual_stats a2 ON cs.app2 = a2.app_name
        )
        SELECT 
            app1,
            app2,
            unique_users,
            total_occurrences,
            days_observed,
            user_percentage,
            app1_individual_users,
            app2_individual_users,
            combination_strength,
            avg_occurrences_per_user,
            popularity_tier,
            CASE 
                WHEN combination_strength >= 80 THEN 'Highly Complementary'
                WHEN combination_strength >= 60 THEN 'Complementary'
                WHEN combination_strength >= 40 THEN 'Moderately Related'
                WHEN combination_strength >= 20 THEN 'Occasionally Related'
                ELSE 'Rarely Related'
            END as relationship_strength
        FROM combination_analysis
        ORDER BY combination_strength DESC, unique_users DESC
        LIMIT ?
        """
        
        params = (time_window_hours, min_users, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "common_app_combinations",
                "status": "success",
                "message": "No common app combinations found with the specified criteria",
                "data": {
                    "combinations": [],
                    "total_combinations": 0,
                    "parameters": {
                        "limit": limit,
                        "min_users": min_users,
                        "time_window_hours": time_window_hours
                    }
                }
            }, indent=2)
        
        # Process results
        combinations = []
        total_users_analyzed = 0
        
        for row in results:
            combination_data = {
                "app_pair": {
                    "app1": row[0],
                    "app2": row[1]
                },
                "usage_metrics": {
                    "unique_users": row[2],
                    "total_occurrences": row[3],
                    "days_observed": row[4],
                    "user_percentage": row[5],
                    "avg_occurrences_per_user": row[9]
                },
                "individual_app_stats": {
                    "app1_users": row[6],
                    "app2_users": row[7]
                },
                "relationship_analysis": {
                    "combination_strength": row[8],
                    "popularity_tier": row[10],
                    "relationship_strength": row[11]
                }
            }
            combinations.append(combination_data)
        
        # Calculate summary statistics
        if combinations:
            total_users_analyzed = max(combo["individual_app_stats"]["app1_users"] + 
                                    combo["individual_app_stats"]["app2_users"] 
                                    for combo in combinations)
            
            avg_combination_strength = sum(combo["relationship_analysis"]["combination_strength"] 
                                         for combo in combinations) / len(combinations)
            
            popularity_distribution = {}
            for combo in combinations:
                tier = combo["relationship_analysis"]["popularity_tier"]
                popularity_distribution[tier] = popularity_distribution.get(tier, 0) + 1
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if combinations:
            # Top combination insight
            top_combo = combinations[0]
            insights.append(f"Strongest app combination: {top_combo['app_pair']['app1']} + {top_combo['app_pair']['app2']} "
                          f"({top_combo['relationship_analysis']['combination_strength']}% combination strength)")
            
            # Popular combinations
            very_popular = [c for c in combinations if c["relationship_analysis"]["popularity_tier"] == "Very Popular"]
            if very_popular:
                insights.append(f"Found {len(very_popular)} very popular app combinations used by 50+ users")
            
            # High complementarity
            highly_complementary = [c for c in combinations if c["relationship_analysis"]["relationship_strength"] == "Highly Complementary"]
            if highly_complementary:
                insights.append(f"{len(highly_complementary)} app pairs show high complementarity (80%+ users use both)")
            
            # Recommendations
            if very_popular:
                recommendations.append("Consider creating app bundles or integration features for very popular combinations")
            
            if highly_complementary:
                recommendations.append("Focus on seamless data sharing between highly complementary apps")
            
            recommendations.append("Monitor emerging combinations for potential new user workflows")
            recommendations.append("Use combination data to improve app recommendation algorithms")
        
        response_data = {
            "tool": "common_app_combinations",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "combinations": combinations,
                "summary": {
                    "total_combinations": len(combinations),
                    "parameters_used": {
                        "limit": limit,
                        "min_users": min_users,
                        "time_window_hours": time_window_hours
                    },
                    "analysis_period": "Last 90 days",
                    "avg_combination_strength": round(avg_combination_strength, 2) if combinations else 0,
                    "popularity_distribution": popularity_distribution if combinations else {}
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed {len(combinations)} common app combinations")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in common_app_combinations: {e}")
        return json.dumps({
            "tool": "common_app_combinations",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze common app combinations"
        }, indent=2)
