"""
Tool: Legacy vs Modern
Category: Version Tracking
Feature ID: 34

Description:
    Compare legacy vs modern application versions. This tool analyzes
    usage patterns between older and newer versions of applications,
    providing insights into adoption rates and migration patterns.

Parameters:
    - app_name (str, optional): Filter by specific application name
    - legacy_threshold_months (int, optional): Months to consider a version legacy (default: 12)
    - limit (int, optional): Maximum number of applications to analyze (default: 50)

Returns:
    - Dictionary with legacy vs modern version comparison analytics

Examples:
    Basic usage:
    Input: {}
    Output: Legacy vs modern comparison for all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "legacy_threshold_months": 6}
    Output: Chrome legacy vs modern version analysis with 6-month threshold

Database Tables Used:
    - app_usage: For usage statistics by version
    - app_list: For application metadata and release dates

Related Tools:
    - version_usage_breakdown: Detailed version usage statistics
    - outdated_versions: Identify specifically outdated versions

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query
from shared.date_utils import days_ago

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def legacy_vs_modern(
    app_name: Optional[str] = None,
    legacy_threshold_months: int = 12,
    limit: int = 50,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Compare legacy vs modern application versions.
    
    Args:
        app_name: Filter by specific application name
        legacy_threshold_months: Months to consider a version legacy (default: 12, max: 36)
        limit: Maximum number of applications to analyze (default: 50, max: 200)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing legacy vs modern version comparison analytics
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing legacy vs modern versions {filter_desc}, threshold: {legacy_threshold_months} months")
        
        # Validate parameters
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        
        if legacy_threshold_months < 1 or legacy_threshold_months > 36:
            raise ValueError("legacy_threshold_months must be between 1 and 36")
        
        # Calculate legacy cutoff date
        legacy_cutoff_date = days_ago(legacy_threshold_months * 30)  # Approximate months to days
        
        if ctx:
            ctx.debug(f"Using legacy cutoff date: {legacy_cutoff_date}")
            ctx.report_progress(25, 100, "Analyzing version age patterns...")
        
        # Build query to get version usage with release date information
        base_query = """
        SELECT 
            u.application_name,
            u.application_version,
            COUNT(*) as usage_sessions,
            COUNT(DISTINCT u.user) as unique_users,
            SUM(u.duration_seconds) as total_seconds,
            l.app_type,
            l.publisher,
            l.current_version,
            l.released_date as app_released_date,
            CASE 
                WHEN l.released_date < ? THEN 'legacy'
                ELSE 'modern'
            END as version_category,
            CASE WHEN u.application_version = l.current_version THEN 1 ELSE 0 END as is_current_version
        FROM app_usage u
        LEFT JOIN app_list l ON u.application_name = l.app_name
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['u.application_name'] = app_name
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="u.application_name, u.application_version",
            order_by="u.application_name ASC, usage_sessions DESC",
            limit=limit * 10  # Get more data to analyze properly
        )
        
        # Add legacy cutoff date as first parameter
        params = (legacy_cutoff_date,) + params
        
        if ctx:
            ctx.debug("Executing legacy vs modern analysis query")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} version records in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing legacy vs modern comparison...")
        
        # Process and categorize data
        app_analysis = {}
        overall_stats = {
            'legacy_sessions': 0,
            'modern_sessions': 0,
            'legacy_hours': 0,
            'modern_hours': 0,
            'legacy_users': set(),
            'modern_users': set(),
            'total_apps_analyzed': 0
        }
        
        for record in result.data:
            app_name_key = record["application_name"]
            
            if app_name_key not in app_analysis:
                app_analysis[app_name_key] = {
                    'app_name': app_name_key,
                    'app_type': record["app_type"],
                    'publisher': record["publisher"],
                    'current_version': record["current_version"],
                    'legacy_versions': [],
                    'modern_versions': [],
                    'legacy_stats': {'sessions': 0, 'hours': 0, 'users': set()},
                    'modern_stats': {'sessions': 0, 'hours': 0, 'users': set()}
                }
            
            app_data = app_analysis[app_name_key]
            version_hours = (record["total_seconds"] or 0) / 3600
            
            version_info = {
                'version': record["application_version"],
                'sessions': record["usage_sessions"],
                'unique_users': record["unique_users"],
                'total_hours': round(version_hours, 2),
                'is_current': bool(record["is_current_version"])
            }
            
            if record["version_category"] == 'legacy':
                app_data['legacy_versions'].append(version_info)
                app_data['legacy_stats']['sessions'] += record["usage_sessions"]
                app_data['legacy_stats']['hours'] += version_hours
                overall_stats['legacy_sessions'] += record["usage_sessions"]
                overall_stats['legacy_hours'] += version_hours
            else:
                app_data['modern_versions'].append(version_info)
                app_data['modern_stats']['sessions'] += record["usage_sessions"]
                app_data['modern_stats']['hours'] += version_hours
                overall_stats['modern_sessions'] += record["usage_sessions"]
                overall_stats['modern_hours'] += version_hours
        
        # Limit to requested number of applications
        limited_apps = dict(list(app_analysis.items())[:limit])
        overall_stats['total_apps_analyzed'] = len(limited_apps)
        
        # Format response
        response_data = {
            "tool": "legacy_vs_modern",
            "description": "Legacy vs modern application version comparison",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "app_name_filter": app_name,
                "legacy_threshold_months": legacy_threshold_months,
                "legacy_cutoff_date": legacy_cutoff_date,
                "applications_analyzed": len(limited_apps)
            },
            "overall_comparison": {
                "legacy_usage": {
                    "total_sessions": overall_stats['legacy_sessions'],
                    "total_hours": round(overall_stats['legacy_hours'], 2),
                    "percentage_of_sessions": round((overall_stats['legacy_sessions'] / (overall_stats['legacy_sessions'] + overall_stats['modern_sessions']) * 100), 2) if (overall_stats['legacy_sessions'] + overall_stats['modern_sessions']) > 0 else 0
                },
                "modern_usage": {
                    "total_sessions": overall_stats['modern_sessions'],
                    "total_hours": round(overall_stats['modern_hours'], 2),
                    "percentage_of_sessions": round((overall_stats['modern_sessions'] / (overall_stats['legacy_sessions'] + overall_stats['modern_sessions']) * 100), 2) if (overall_stats['legacy_sessions'] + overall_stats['modern_sessions']) > 0 else 0
                }
            },
            "application_analysis": []
        }
        
        # Process each application
        for app_name_key, app_data in limited_apps.items():
            total_app_sessions = app_data['legacy_stats']['sessions'] + app_data['modern_stats']['sessions']
            total_app_hours = app_data['legacy_stats']['hours'] + app_data['modern_stats']['hours']
            
            app_comparison = {
                "application_name": app_data['app_name'],
                "app_type": app_data['app_type'],
                "publisher": app_data['publisher'],
                "current_version": app_data['current_version'],
                "version_breakdown": {
                    "legacy_versions_count": len(app_data['legacy_versions']),
                    "modern_versions_count": len(app_data['modern_versions']),
                    "total_versions": len(app_data['legacy_versions']) + len(app_data['modern_versions'])
                },
                "usage_comparison": {
                    "legacy": {
                        "sessions": app_data['legacy_stats']['sessions'],
                        "hours": round(app_data['legacy_stats']['hours'], 2),
                        "percentage": round((app_data['legacy_stats']['sessions'] / total_app_sessions * 100), 2) if total_app_sessions > 0 else 0
                    },
                    "modern": {
                        "sessions": app_data['modern_stats']['sessions'],
                        "hours": round(app_data['modern_stats']['hours'], 2),
                        "percentage": round((app_data['modern_stats']['sessions'] / total_app_sessions * 100), 2) if total_app_sessions > 0 else 0
                    }
                },
                "migration_insight": "High legacy usage" if (app_data['legacy_stats']['sessions'] / total_app_sessions > 0.5 if total_app_sessions > 0 else False) else "Good modern adoption"
            }
            
            response_data["application_analysis"].append(app_comparison)
        
        # Add summary insights
        total_sessions = overall_stats['legacy_sessions'] + overall_stats['modern_sessions']
        response_data["insights"] = {
            "legacy_dominance": overall_stats['legacy_sessions'] > overall_stats['modern_sessions'],
            "migration_needed": overall_stats['legacy_sessions'] / total_sessions > 0.3 if total_sessions > 0 else False,
            "well_migrated_apps": len([app for app in response_data["application_analysis"] if app["usage_comparison"]["modern"]["percentage"] > 70]),
            "legacy_heavy_apps": len([app for app in response_data["application_analysis"] if app["usage_comparison"]["legacy"]["percentage"] > 50])
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Legacy vs modern analysis complete")
            ctx.info(f"Analysis complete: {len(limited_apps)} apps, {overall_stats['legacy_sessions']} legacy vs {overall_stats['modern_sessions']} modern sessions")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in legacy_vs_modern: {e}")
        if ctx:
            ctx.error(f"Failed to analyze legacy vs modern versions: {e}")
        
        return {
            "tool": "legacy_vs_modern",
            "error": str(e),
            "message": "Failed to analyze legacy vs modern versions"
        }
