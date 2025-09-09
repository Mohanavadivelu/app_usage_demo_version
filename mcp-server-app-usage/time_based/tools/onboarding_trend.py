"""
Tool: Onboarding Trend
Category: Time Based
Feature ID: 54

Description:
    Track new application adoptions - analyzes how users discover and adopt
    new applications over time with detailed onboarding success metrics.

Parameters:
    - start_date (str, optional): Start date for analysis (YYYY-MM-DD format)
    - end_date (str, optional): End date for analysis (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of applications to analyze (default: 100)
    - min_adopters (int, optional): Minimum number of adopters to include app (default: 5)

Returns:
    - Track new application adoptions with detailed analytics

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
async def onboarding_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
    min_adopters: Optional[int] = 5
) -> str:
    """
    Track new application adoptions and onboarding trends.
    
    Analyzes how users discover and adopt new applications over time,
    providing insights into onboarding success and adoption patterns.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format, optional)
        end_date: End date for analysis (YYYY-MM-DD format, optional)
        limit: Maximum number of applications to analyze (default: 100)
        min_adopters: Minimum number of adopters to include app (default: 5)
    
    Returns:
        JSON string containing application adoption trends with detailed analytics
    """
    try:
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")
        if min_adopters is not None and (min_adopters < 1 or min_adopters > 100):
            raise ValueError("min_adopters must be between 1 and 100")
        
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
        min_adopters = min_adopters or 5
        
        # Set default date range if not provided (last 90 days)
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        elif not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        elif not start_date:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
        
        logger.info(f"Analyzing onboarding trends from {start_date} to {end_date} with limit={limit}, min_adopters={min_adopters}")
        
        # Query to analyze application adoption and onboarding trends
        query = """
        WITH user_app_first_usage AS (
            SELECT 
                user_id,
                app_name,
                MIN(timestamp) as first_usage_date,
                COUNT(*) as first_day_sessions,
                SUM(duration_minutes) as first_day_duration,
                MAX(timestamp) as last_usage_date
            FROM app_usage
            WHERE DATE(timestamp) BETWEEN ? AND ?
            GROUP BY user_id, app_name
        ),
        app_adoption_metrics AS (
            SELECT 
                app_name,
                COUNT(DISTINCT user_id) as total_adopters,
                MIN(first_usage_date) as first_adoption_date,
                MAX(first_usage_date) as latest_adoption_date,
                ROUND(AVG(first_day_sessions), 2) as avg_first_day_sessions,
                ROUND(AVG(first_day_duration), 2) as avg_first_day_duration,
                SUM(first_day_sessions) as total_first_day_sessions,
                SUM(first_day_duration) as total_first_day_duration
            FROM user_app_first_usage
            GROUP BY app_name
            HAVING COUNT(DISTINCT user_id) >= ?
        ),
        retention_analysis AS (
            SELECT 
                aam.app_name,
                aam.total_adopters,
                aam.first_adoption_date,
                aam.latest_adoption_date,
                aam.avg_first_day_sessions,
                aam.avg_first_day_duration,
                aam.total_first_day_sessions,
                aam.total_first_day_duration,
                COUNT(CASE WHEN uafu.last_usage_date > DATE(uafu.first_usage_date, '+7 days') THEN 1 END) as week_1_retained,
                COUNT(CASE WHEN uafu.last_usage_date > DATE(uafu.first_usage_date, '+30 days') THEN 1 END) as month_1_retained,
                ROUND(
                    COUNT(CASE WHEN uafu.last_usage_date > DATE(uafu.first_usage_date, '+7 days') THEN 1 END) * 100.0 / aam.total_adopters,
                    2
                ) as week_1_retention_rate,
                ROUND(
                    COUNT(CASE WHEN uafu.last_usage_date > DATE(uafu.first_usage_date, '+30 days') THEN 1 END) * 100.0 / aam.total_adopters,
                    2
                ) as month_1_retention_rate,
                julianday(aam.latest_adoption_date) - julianday(aam.first_adoption_date) as adoption_period_days
            FROM app_adoption_metrics aam
            JOIN user_app_first_usage uafu ON aam.app_name = uafu.app_name
            GROUP BY aam.app_name, aam.total_adopters, aam.first_adoption_date, aam.latest_adoption_date,
                     aam.avg_first_day_sessions, aam.avg_first_day_duration, aam.total_first_day_sessions, aam.total_first_day_duration
        ),
        trend_analysis AS (
            SELECT 
                *,
                CASE 
                    WHEN total_adopters >= 100 THEN 'High Adoption'
                    WHEN total_adopters >= 50 THEN 'Moderate Adoption'
                    WHEN total_adopters >= 20 THEN 'Low Adoption'
                    ELSE 'Very Low Adoption'
                END as adoption_level,
                CASE 
                    WHEN avg_first_day_duration >= 60 THEN 'High Engagement'
                    WHEN avg_first_day_duration >= 30 THEN 'Moderate Engagement'
                    WHEN avg_first_day_duration >= 15 THEN 'Low Engagement'
                    ELSE 'Very Low Engagement'
                END as onboarding_engagement,
                CASE 
                    WHEN week_1_retention_rate >= 50 THEN 'Excellent Retention'
                    WHEN week_1_retention_rate >= 30 THEN 'Good Retention'
                    WHEN week_1_retention_rate >= 15 THEN 'Fair Retention'
                    ELSE 'Poor Retention'
                END as retention_quality,
                CASE 
                    WHEN adoption_period_days <= 7 THEN 'Rapid Adoption'
                    WHEN adoption_period_days <= 30 THEN 'Steady Adoption'
                    WHEN adoption_period_days <= 90 THEN 'Gradual Adoption'
                    ELSE 'Slow Adoption'
                END as adoption_speed,
                ROUND(total_adopters / NULLIF(adoption_period_days, 0), 2) as daily_adoption_rate
            FROM retention_analysis
        )
        SELECT 
            app_name,
            total_adopters,
            first_adoption_date,
            latest_adoption_date,
            avg_first_day_sessions,
            avg_first_day_duration,
            total_first_day_sessions,
            total_first_day_duration,
            week_1_retained,
            month_1_retained,
            week_1_retention_rate,
            month_1_retention_rate,
            adoption_period_days,
            adoption_level,
            onboarding_engagement,
            retention_quality,
            adoption_speed,
            daily_adoption_rate
        FROM trend_analysis
        ORDER BY total_adopters DESC, week_1_retention_rate DESC
        LIMIT ?
        """
        
        params = (start_date, end_date, min_adopters, limit)
        results = execute_analytics_query(query, params)
        
        if not results:
            return json.dumps({
                "tool": "onboarding_trend",
                "status": "success",
                "message": "No application adoption data found for the specified period",
                "data": {
                    "applications": [],
                    "total_applications": 0,
                    "parameters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "min_adopters": min_adopters
                    }
                }
            }, indent=2)
        
        # Process results
        applications = []
        adoption_level_distribution = {}
        onboarding_engagement_distribution = {}
        retention_quality_distribution = {}
        adoption_speed_distribution = {}
        
        for row in results:
            app_data = {
                "app_name": row[0],
                "adoption_metrics": {
                    "total_adopters": row[1],
                    "first_adoption_date": row[2],
                    "latest_adoption_date": row[3],
                    "adoption_period_days": row[12],
                    "daily_adoption_rate": row[17]
                },
                "onboarding_analysis": {
                    "avg_first_day_sessions": row[4],
                    "avg_first_day_duration": row[5],
                    "total_first_day_sessions": row[6],
                    "total_first_day_duration": row[7]
                },
                "retention_metrics": {
                    "week_1_retained": row[8],
                    "month_1_retained": row[9],
                    "week_1_retention_rate": row[10],
                    "month_1_retention_rate": row[11]
                },
                "classification": {
                    "adoption_level": row[13],
                    "onboarding_engagement": row[14],
                    "retention_quality": row[15],
                    "adoption_speed": row[16]
                }
            }
            applications.append(app_data)
            
            # Update distributions
            adoption_level = row[13]
            onboarding_engagement = row[14]
            retention_quality = row[15]
            adoption_speed = row[16]
            
            adoption_level_distribution[adoption_level] = adoption_level_distribution.get(adoption_level, 0) + 1
            onboarding_engagement_distribution[onboarding_engagement] = onboarding_engagement_distribution.get(onboarding_engagement, 0) + 1
            retention_quality_distribution[retention_quality] = retention_quality_distribution.get(retention_quality, 0) + 1
            adoption_speed_distribution[adoption_speed] = adoption_speed_distribution.get(adoption_speed, 0) + 1
        
        # Calculate summary statistics
        if applications:
            total_applications = len(applications)
            total_adopters_across_apps = sum(app["adoption_metrics"]["total_adopters"] for app in applications)
            avg_adopters_per_app = round(total_adopters_across_apps / total_applications, 2)
            
            avg_first_day_engagement = sum(app["onboarding_analysis"]["avg_first_day_duration"] for app in applications) / total_applications
            avg_week_1_retention = sum(app["retention_metrics"]["week_1_retention_rate"] for app in applications) / total_applications
            
            top_adoption_app = max(applications, key=lambda x: x["adoption_metrics"]["total_adopters"])
            best_retention_app = max(applications, key=lambda x: x["retention_metrics"]["week_1_retention_rate"])
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if applications:
            insights.append(f"Analyzed {total_applications} applications with {total_adopters_across_apps} total adopters")
            insights.append(f"Average {avg_adopters_per_app} adopters per application")
            insights.append(f"Top adoption: {top_adoption_app['app_name']} with {top_adoption_app['adoption_metrics']['total_adopters']} adopters")
            insights.append(f"Best retention: {best_retention_app['app_name']} with {best_retention_app['retention_metrics']['week_1_retention_rate']}% week-1 retention")
            insights.append(f"Average first-day engagement: {round(avg_first_day_engagement, 1)} minutes")
            insights.append(f"Average week-1 retention rate: {round(avg_week_1_retention, 1)}%")
            
            # Distribution insights
            high_adoption = adoption_level_distribution.get('High Adoption', 0)
            excellent_retention = retention_quality_distribution.get('Excellent Retention', 0)
            high_engagement = onboarding_engagement_distribution.get('High Engagement', 0)
            rapid_adoption = adoption_speed_distribution.get('Rapid Adoption', 0)
            
            if high_adoption > 0:
                insights.append(f"{high_adoption} applications show high adoption (100+ users)")
            if excellent_retention > 0:
                insights.append(f"{excellent_retention} applications have excellent retention (50%+ week-1)")
            if high_engagement > 0:
                insights.append(f"{high_engagement} applications show high onboarding engagement (60+ minutes)")
            if rapid_adoption > 0:
                insights.append(f"{rapid_adoption} applications achieved rapid adoption (within 7 days)")
            
            # Recommendations
            if avg_week_1_retention < 25:
                recommendations.append("Focus on improving week-1 retention across applications")
                recommendations.append("Implement better onboarding flows and user guidance")
            
            if avg_first_day_engagement < 30:
                recommendations.append("Enhance first-day user experience to increase engagement")
                recommendations.append("Consider interactive tutorials or guided tours")
            
            if excellent_retention > 0:
                recommendations.append("Study high-retention apps to identify best practices")
                recommendations.append("Apply successful retention strategies to other applications")
            
            if high_adoption > 0:
                recommendations.append("Analyze high-adoption apps for successful launch strategies")
                recommendations.append("Replicate marketing and positioning approaches")
            
            recommendations.append("Monitor onboarding metrics continuously for early intervention")
            recommendations.append("A/B test different onboarding approaches to optimize adoption")
            recommendations.append("Create user cohorts based on adoption patterns for targeted engagement")
        
        response_data = {
            "tool": "onboarding_trend",
            "status": "success",
            "timestamp": "2025-01-08T00:00:00Z",
            "data": {
                "applications": applications,
                "summary": {
                    "total_applications": len(applications),
                    "analysis_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "parameters_used": {
                        "limit": limit,
                        "min_adopters": min_adopters
                    },
                    "statistics": {
                        "total_adopters_across_apps": total_adopters_across_apps if applications else 0,
                        "avg_adopters_per_app": avg_adopters_per_app if applications else 0,
                        "avg_first_day_engagement_minutes": round(avg_first_day_engagement, 2) if applications else 0,
                        "avg_week_1_retention_rate": round(avg_week_1_retention, 2) if applications else 0
                    },
                    "distributions": {
                        "adoption_levels": adoption_level_distribution,
                        "onboarding_engagement": onboarding_engagement_distribution,
                        "retention_quality": retention_quality_distribution,
                        "adoption_speed": adoption_speed_distribution
                    }
                },
                "insights": insights,
                "recommendations": recommendations
            }
        }
        
        logger.info(f"Successfully analyzed onboarding trends for {len(applications)} applications")
        return json.dumps(response_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in onboarding_trend: {e}")
        return json.dumps({
            "tool": "onboarding_trend",
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze onboarding trends"
        }, indent=2)
