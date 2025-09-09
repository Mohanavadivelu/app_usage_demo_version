"""
Tool: Total Usage Period
Category: Usage Stats
Feature ID: 62

Description:
    Calculate total usage time for time periods with comprehensive analytics

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - period_type (str, optional): Aggregation period ('daily', 'weekly', 'monthly', default: 'daily')
    - platform (str, optional): Platform to filter by
    - application_name (str, optional): Specific application to analyze

Returns:
    - Total usage time aggregated by time periods with detailed analytics and trends

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-09
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Import the mcp instance from server_instance module
from server_instance import mcp
from shared.database_utils import get_database_connection
from shared.date_utils import validate_date_range, format_date_for_db

logger = logging.getLogger(__name__)


@mcp.tool()
async def total_usage_period(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period_type: Optional[str] = "daily",
    platform: Optional[str] = None,
    application_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate total usage time for time periods with comprehensive analytics.
    
    Provides detailed insights into usage patterns over time, including:
    - Total usage time aggregated by periods
    - User engagement trends
    - Application diversity metrics
    - Session activity patterns
    - Growth and trend analysis
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        period_type: Aggregation period ('daily', 'weekly', 'monthly', default: 'daily')
        platform: Platform to filter by (e.g., 'Windows', 'macOS', 'Linux')
        application_name: Specific application to analyze
    
    Returns:
        Dict containing usage time aggregated by periods with analytics and insights
    """
    try:
        # Parameter validation
        valid_period_types = ['daily', 'weekly', 'monthly']
        if period_type and period_type not in valid_period_types:
            return {
                "status": "error",
                "message": f"period_type must be one of: {', '.join(valid_period_types)}"
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
        period_type = period_type or "daily"
        
        # Build period grouping based on type
        if period_type == "daily":
            period_group = "log_date"
            period_format = "log_date"
        elif period_type == "weekly":
            period_group = "strftime('%Y-W%W', log_date)"
            period_format = "strftime('%Y-W%W', log_date) as period"
        else:  # monthly
            period_group = "strftime('%Y-%m', log_date)"
            period_format = "strftime('%Y-%m', log_date) as period"
        
        # Build query with CTEs for comprehensive analysis
        query = f"""
        WITH period_usage AS (
            SELECT 
                {period_format},
                log_date,
                SUM(duration_seconds) as total_seconds,
                COUNT(DISTINCT user) as unique_users,
                COUNT(DISTINCT application_name) as unique_apps,
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_session_seconds,
                MIN(duration_seconds) as min_session_seconds,
                MAX(duration_seconds) as max_session_seconds
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
        
        # Add application filter
        if application_name:
            query += " AND application_name = ?"
            params.append(application_name)
        
        query += f"""
            GROUP BY {period_group}
        ),
        period_stats AS (
            SELECT 
                pu.*,
                SUM(total_seconds) OVER () as grand_total_seconds,
                SUM(unique_users) OVER () as grand_total_users,
                SUM(total_sessions) OVER () as grand_total_sessions,
                COUNT(*) OVER () as total_periods,
                AVG(total_seconds) OVER () as avg_period_seconds,
                LAG(total_seconds) OVER (ORDER BY {"log_date" if period_type == "daily" else "period"}) as prev_period_seconds,
                ROW_NUMBER() OVER (ORDER BY total_seconds DESC) as usage_rank,
                ROW_NUMBER() OVER (ORDER BY unique_users DESC) as user_rank,
                ROW_NUMBER() OVER (ORDER BY total_sessions DESC) as session_rank
            FROM period_usage pu
        )
        SELECT 
            {"period" if period_type != "daily" else "log_date as period"},
            log_date,
            total_seconds,
            unique_users,
            unique_apps,
            total_sessions,
            avg_session_seconds,
            min_session_seconds,
            max_session_seconds,
            grand_total_seconds,
            grand_total_users,
            grand_total_sessions,
            total_periods,
            avg_period_seconds,
            prev_period_seconds,
            usage_rank,
            user_rank,
            session_rank
        FROM period_stats
        ORDER BY {"log_date" if period_type == "daily" else "period"}
        """
        
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
                    "tool": "total_usage_period",
                    "description": "Calculate total usage time for time periods",
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "period_type": period_type,
                        "platform": platform,
                        "application_name": application_name
                    },
                    "query_time_ms": round(query_time, 2),
                    "total_records": 0,
                    "periods": []
                },
                "insights": {
                    "summary": "No usage data found for the specified criteria",
                    "recommendations": [
                        "Try expanding the date range for analysis",
                        "Check if the specified platform has recorded usage data",
                        "Verify the application name if filtering by specific app"
                    ]
                }
            }
        
        # Process results
        periods = []
        grand_total_seconds = results[0][9] if results else 0
        grand_total_users = results[0][10] if results else 0
        grand_total_sessions = results[0][11] if results else 0
        total_periods = results[0][12] if results else 0
        avg_period_seconds = results[0][13] if results else 0
        
        for row in results:
            # Calculate growth rate
            growth_rate = None
            if row[14] is not None and row[14] > 0:  # prev_period_seconds
                growth_rate = round(((row[2] - row[14]) / row[14]) * 100, 2)
            
            period_data = {
                "period": row[0],
                "date": row[1] if period_type == "daily" else None,
                "usage_metrics": {
                    "total_hours": round(row[2] / 3600, 2),  # total_seconds to hours
                    "total_minutes": round(row[2] / 60, 2),  # total_seconds to minutes
                    "percentage_of_total": round((row[2] / grand_total_seconds) * 100, 2) if grand_total_seconds > 0 else 0,
                    "usage_rank": int(row[15]),  # usage_rank
                    "vs_average": round(((row[2] - avg_period_seconds) / avg_period_seconds) * 100, 2) if avg_period_seconds > 0 else 0
                },
                "user_metrics": {
                    "unique_users": int(row[3]),
                    "user_rank": int(row[16]),  # user_rank
                    "percentage_of_total_users": round((row[3] / grand_total_users) * 100, 2) if grand_total_users > 0 else 0
                },
                "activity_metrics": {
                    "unique_apps": int(row[4]),
                    "total_sessions": int(row[5]),
                    "session_rank": int(row[17]),  # session_rank
                    "avg_session_minutes": round(row[6] / 60, 2),  # avg_session_seconds to minutes
                    "min_session_minutes": round(row[7] / 60, 2),  # min_session_seconds to minutes
                    "max_session_minutes": round(row[8] / 60, 2),  # max_session_seconds to minutes
                    "sessions_per_user": round(row[5] / row[3], 2) if row[3] > 0 else 0
                },
                "trend_analysis": {
                    "growth_rate_percentage": growth_rate,
                    "trend_direction": "up" if growth_rate and growth_rate > 0 else "down" if growth_rate and growth_rate < 0 else "stable"
                }
            }
            periods.append(period_data)
        
        # Generate insights
        peak_period = max(periods, key=lambda x: x['usage_metrics']['total_hours']) if periods else None
        low_period = min(periods, key=lambda x: x['usage_metrics']['total_hours']) if periods else None
        
        # Calculate trend analysis
        positive_growth_periods = [p for p in periods if p['trend_analysis']['growth_rate_percentage'] and p['trend_analysis']['growth_rate_percentage'] > 0]
        negative_growth_periods = [p for p in periods if p['trend_analysis']['growth_rate_percentage'] and p['trend_analysis']['growth_rate_percentage'] < 0]
        
        insights = {
            "summary": f"Analysis of {len(periods)} {period_type} periods showing usage patterns over time",
            "key_findings": [],
            "period_analysis": {
                "total_periods_analyzed": len(periods),
                "period_type": period_type,
                "total_usage_hours": round(grand_total_seconds / 3600, 2),
                "total_unique_users": grand_total_users,
                "total_sessions": grand_total_sessions,
                "average_usage_per_period_hours": round(avg_period_seconds / 3600, 2)
            },
            "trend_analysis": {
                "periods_with_growth": len(positive_growth_periods),
                "periods_with_decline": len(negative_growth_periods),
                "growth_trend": "positive" if len(positive_growth_periods) > len(negative_growth_periods) else "negative" if len(negative_growth_periods) > len(positive_growth_periods) else "mixed"
            },
            "recommendations": []
        }
        
        if peak_period and low_period:
            insights["key_findings"].extend([
                f"Peak usage period: {peak_period['period']} with {peak_period['usage_metrics']['total_hours']} hours",
                f"Lowest usage period: {low_period['period']} with {low_period['usage_metrics']['total_hours']} hours",
                f"Usage variation: {round(((peak_period['usage_metrics']['total_hours'] - low_period['usage_metrics']['total_hours']) / low_period['usage_metrics']['total_hours']) * 100, 1)}% difference between peak and low"
            ])
            
            # User engagement analysis
            peak_user_period = max(periods, key=lambda x: x['user_metrics']['unique_users'])
            insights["key_findings"].append(f"Highest user engagement: {peak_user_period['period']} with {peak_user_period['user_metrics']['unique_users']} unique users")
        
        # Growth trend recommendations
        if insights["trend_analysis"]["growth_trend"] == "positive":
            insights["recommendations"].append("Overall positive growth trend - continue current strategies and scale successful initiatives")
        elif insights["trend_analysis"]["growth_trend"] == "negative":
            insights["recommendations"].append("Declining usage trend detected - investigate causes and implement retention strategies")
        else:
            insights["recommendations"].append("Mixed growth pattern - analyze successful periods to replicate positive factors")
        
        # Activity pattern recommendations
        if periods:
            high_activity_periods = [p for p in periods if p['activity_metrics']['sessions_per_user'] > 3]
            if high_activity_periods:
                insights["recommendations"].append(f"Focus on replicating conditions from {len(high_activity_periods)} high-activity periods (>3 sessions per user)")
            
            diverse_app_periods = [p for p in periods if p['activity_metrics']['unique_apps'] > 5]
            if diverse_app_periods:
                insights["recommendations"].append(f"Promote app diversity - {len(diverse_app_periods)} periods showed healthy app variety (>5 unique apps)")
        
        return {
            "status": "success",
            "data": {
                "tool": "total_usage_period",
                "description": "Calculate total usage time for time periods with comprehensive analytics",
                "parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "period_type": period_type,
                    "platform": platform,
                    "application_name": application_name
                },
                "query_time_ms": round(query_time, 2),
                "total_records": len(periods),
                "periods": periods
            },
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in total_usage_period: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze total usage by period: {str(e)}",
            "tool": "total_usage_period"
        }
