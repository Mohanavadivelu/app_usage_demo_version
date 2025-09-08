"""
Tool: Version Distribution
Category: Version Tracking
Feature ID: 36

Description:
    Version distribution analysis. This tool provides comprehensive
    analytics on how different versions of applications are distributed
    across the user base, including adoption patterns and trends.

Parameters:
    - limit (int, optional): Maximum number of applications to analyze (default: 50)
    - app_name (str, optional): Filter by specific application name
    - include_percentages (bool, optional): Include percentage breakdowns (default: true)
    - min_usage_threshold (int, optional): Minimum usage sessions to include (default: 1)

Returns:
    - Dictionary with version distribution analytics and insights

Examples:
    Basic usage:
    Input: {}
    Output: Version distribution for all applications

    Specific app analysis:
    Input: {"app_name": "Chrome", "min_usage_threshold": 10}
    Output: Chrome version distribution with minimum 10 sessions

Database Tables Used:
    - app_usage: For usage statistics by version
    - app_list: For application metadata

Related Tools:
    - version_usage_breakdown: Detailed version usage statistics
    - legacy_vs_modern: Compare legacy vs modern versions

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def version_distribution(
    limit: int = 50,
    app_name: Optional[str] = None,
    include_percentages: bool = True,
    min_usage_threshold: int = 1,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Analyze version distribution across applications.
    
    Args:
        limit: Maximum number of applications to analyze (default: 50, max: 200)
        app_name: Filter by specific application name
        include_percentages: Include percentage breakdowns (default: true)
        min_usage_threshold: Minimum usage sessions to include (default: 1, max: 1000)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing version distribution analytics and insights
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Analyzing version distribution {filter_desc}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        
        if min_usage_threshold < 1 or min_usage_threshold > 1000:
            raise ValueError("min_usage_threshold must be between 1 and 1000")
        
        # Build query for version distribution analysis
        base_query = """
        SELECT 
            u.application_name,
            u.application_version,
            COUNT(*) as usage_sessions,
            COUNT(DISTINCT u.user) as unique_users,
            SUM(u.duration_seconds) as total_seconds,
            AVG(u.duration_seconds) as avg_session_seconds,
            MIN(u.log_date) as first_usage_date,
            MAX(u.log_date) as last_usage_date,
            l.app_type,
            l.publisher,
            l.current_version,
            CASE WHEN u.application_version = l.current_version THEN 1 ELSE 0 END as is_current_version
        FROM app_usage u
        LEFT JOIN app_list l ON u.application_name = l.app_name
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['u.application_name'] = app_name
        
        # Add minimum usage threshold filter
        having_clause = f"COUNT(*) >= {min_usage_threshold}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="u.application_name, u.application_version",
            having=having_clause,
            order_by="u.application_name ASC, usage_sessions DESC",
            limit=limit * 20  # Get more data to analyze properly
        )
        
        if ctx:
            ctx.debug("Executing version distribution query")
            ctx.report_progress(25, 100, "Querying version distribution data...")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} version records in {result.query_time_ms}ms")
            ctx.report_progress(50, 100, "Processing version distribution analysis...")
        
        # Group data by application
        app_distributions = {}
        overall_stats = {
            'total_sessions': 0,
            'total_hours': 0,
            'unique_apps': set(),
            'total_versions': 0,
            'current_version_sessions': 0,
            'outdated_version_sessions': 0
        }
        
        for record in result.data:
            app_name_key = record["application_name"]
            
            if app_name_key not in app_distributions:
                app_distributions[app_name_key] = {
                    'app_name': app_name_key,
                    'app_type': record["app_type"],
                    'publisher': record["publisher"],
                    'current_version': record["current_version"],
                    'versions': [],
                    'total_app_sessions': 0,
                    'total_app_hours': 0,
                    'unique_app_users': set(),
                    'version_count': 0
                }
            
            app_data = app_distributions[app_name_key]
            version_hours = (record["total_seconds"] or 0) / 3600
            avg_session_minutes = (record["avg_session_seconds"] or 0) / 60
            
            # Add to app totals
            app_data['total_app_sessions'] += record["usage_sessions"]
            app_data['total_app_hours'] += version_hours
            app_data['version_count'] += 1
            
            # Add to overall stats
            overall_stats['total_sessions'] += record["usage_sessions"]
            overall_stats['total_hours'] += version_hours
            overall_stats['unique_apps'].add(app_name_key)
            overall_stats['total_versions'] += 1
            
            if record["is_current_version"]:
                overall_stats['current_version_sessions'] += record["usage_sessions"]
            else:
                overall_stats['outdated_version_sessions'] += record["usage_sessions"]
            
            version_info = {
                'version': record["application_version"],
                'is_current': bool(record["is_current_version"]),
                'usage_sessions': record["usage_sessions"],
                'unique_users': record["unique_users"],
                'total_hours': round(version_hours, 2),
                'average_session_minutes': round(avg_session_minutes, 2),
                'first_usage_date': record["first_usage_date"],
                'last_usage_date': record["last_usage_date"]
            }
            
            app_data['versions'].append(version_info)
        
        # Limit to requested number of applications
        limited_apps = dict(list(app_distributions.items())[:limit])
        
        # Calculate percentages and additional metrics
        response_data = {
            "tool": "version_distribution",
            "description": "Version distribution analysis across applications",
            "query_time_ms": result.query_time_ms,
            "analysis_parameters": {
                "app_name_filter": app_name,
                "applications_analyzed": len(limited_apps),
                "include_percentages": include_percentages,
                "min_usage_threshold": min_usage_threshold
            },
            "overall_statistics": {
                "total_sessions": overall_stats['total_sessions'],
                "total_hours": round(overall_stats['total_hours'], 2),
                "unique_applications": len(overall_stats['unique_apps']),
                "total_versions": overall_stats['total_versions'],
                "current_version_adoption": {
                    "sessions": overall_stats['current_version_sessions'],
                    "percentage": round((overall_stats['current_version_sessions'] / overall_stats['total_sessions'] * 100), 2) if overall_stats['total_sessions'] > 0 else 0
                },
                "outdated_version_usage": {
                    "sessions": overall_stats['outdated_version_sessions'],
                    "percentage": round((overall_stats['outdated_version_sessions'] / overall_stats['total_sessions'] * 100), 2) if overall_stats['total_sessions'] > 0 else 0
                }
            },
            "application_distributions": []
        }
        
        # Process each application's distribution
        for app_name_key, app_data in limited_apps.items():
            # Sort versions by usage
            app_data['versions'].sort(key=lambda x: x['usage_sessions'], reverse=True)
            
            # Calculate percentages if requested
            if include_percentages:
                for version in app_data['versions']:
                    version['percentage_of_app_usage'] = round(
                        (version['usage_sessions'] / app_data['total_app_sessions'] * 100), 2
                    ) if app_data['total_app_sessions'] > 0 else 0
            
            # Identify distribution patterns
            current_version_usage = sum(v['usage_sessions'] for v in app_data['versions'] if v['is_current'])
            current_version_percentage = (current_version_usage / app_data['total_app_sessions'] * 100) if app_data['total_app_sessions'] > 0 else 0
            
            # Determine distribution pattern
            if current_version_percentage > 80:
                distribution_pattern = "well_adopted"
            elif current_version_percentage > 50:
                distribution_pattern = "moderately_adopted"
            elif current_version_percentage > 20:
                distribution_pattern = "fragmented"
            else:
                distribution_pattern = "highly_fragmented"
            
            app_distribution = {
                "application_name": app_data['app_name'],
                "app_type": app_data['app_type'],
                "publisher": app_data['publisher'],
                "current_version": app_data['current_version'],
                "distribution_summary": {
                    "total_versions": app_data['version_count'],
                    "total_sessions": app_data['total_app_sessions'],
                    "total_hours": round(app_data['total_app_hours'], 2),
                    "current_version_adoption_percentage": round(current_version_percentage, 2),
                    "distribution_pattern": distribution_pattern
                },
                "version_breakdown": app_data['versions']
            }
            
            response_data["application_distributions"].append(app_distribution)
        
        if ctx:
            ctx.report_progress(75, 100, "Generating distribution insights...")
        
        # Add insights and patterns
        response_data["insights"] = {
            "adoption_patterns": {
                "well_adopted_apps": len([app for app in response_data["application_distributions"] 
                                        if app["distribution_summary"]["distribution_pattern"] == "well_adopted"]),
                "fragmented_apps": len([app for app in response_data["application_distributions"] 
                                      if app["distribution_summary"]["distribution_pattern"] in ["fragmented", "highly_fragmented"]]),
                "average_versions_per_app": round(sum(app["distribution_summary"]["total_versions"] 
                                                    for app in response_data["application_distributions"]) / len(response_data["application_distributions"]), 2) if response_data["application_distributions"] else 0
            },
            "top_fragmented_apps": [
                {
                    "app": app["application_name"],
                    "versions": app["distribution_summary"]["total_versions"],
                    "current_adoption": app["distribution_summary"]["current_version_adoption_percentage"]
                }
                for app in sorted(response_data["application_distributions"], 
                                key=lambda x: x["distribution_summary"]["total_versions"], reverse=True)
            ][:5],
            "best_adoption_apps": [
                {
                    "app": app["application_name"],
                    "current_adoption": app["distribution_summary"]["current_version_adoption_percentage"],
                    "total_sessions": app["distribution_summary"]["total_sessions"]
                }
                for app in sorted(response_data["application_distributions"], 
                                key=lambda x: x["distribution_summary"]["current_version_adoption_percentage"], reverse=True)
            ][:5]
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Version distribution analysis complete")
            ctx.info(f"Analysis complete: {len(limited_apps)} apps, {overall_stats['total_versions']} total versions")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in version_distribution: {e}")
        if ctx:
            ctx.error(f"Failed to analyze version distribution: {e}")
        
        return {
            "tool": "version_distribution",
            "error": str(e),
            "message": "Failed to analyze version distribution"
        }
