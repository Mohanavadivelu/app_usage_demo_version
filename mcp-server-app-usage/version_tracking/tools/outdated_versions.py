"""
Tool: Outdated Versions
Category: Version Tracking
Feature ID: 35

Description:
    Identify outdated application versions. This tool finds applications
    that are not running the current/latest version and provides insights
    into version lag and potential security or performance issues.

Parameters:
    - limit (int, optional): Maximum number of results to return (default: 100)
    - app_name (str, optional): Filter by specific application name
    - sort_by (str, optional): Sort field (usage_sessions, version_lag_days, unique_users)
    - sort_order (str, optional): Sort order (asc, desc)

Returns:
    - Dictionary with outdated version analysis and recommendations

Examples:
    Basic usage:
    Input: {}
    Output: List of all outdated application versions

    Specific app analysis:
    Input: {"app_name": "Chrome", "sort_by": "version_lag_days"}
    Output: Chrome outdated versions sorted by how old they are

Database Tables Used:
    - app_usage: For usage statistics by version
    - app_list: For current version information

Related Tools:
    - version_usage_breakdown: Detailed version usage statistics
    - legacy_vs_modern: Compare legacy vs modern versions

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query, build_query

logger = logging.getLogger(__name__)

# Import the mcp instance from server_instance module
from server_instance import mcp


@mcp.tool()
async def outdated_versions(
    limit: int = 100,
    app_name: Optional[str] = None,
    sort_by: str = "usage_sessions",
    sort_order: str = "desc",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Identify outdated application versions.
    
    Args:
        limit: Maximum number of results to return (default: 100, max: 1000)
        app_name: Filter by specific application name
        sort_by: Field to sort by (usage_sessions, version_lag_days, unique_users, total_hours)
        sort_order: Sort order (asc, desc)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing outdated version analysis and recommendations
    """
    try:
        if ctx:
            filter_desc = f"for {app_name}" if app_name else "for all applications"
            ctx.info(f"Identifying outdated versions {filter_desc}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        valid_sort_fields = ['usage_sessions', 'version_lag_days', 'unique_users', 'total_hours']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        
        # Build query to find outdated versions
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
            l.released_date as current_version_release_date,
            CASE 
                WHEN u.application_version != l.current_version THEN 1 
                ELSE 0 
            END as is_outdated,
            CASE 
                WHEN l.released_date IS NOT NULL THEN 
                    CAST((julianday('now') - julianday(l.released_date)) AS INTEGER)
                ELSE NULL 
            END as version_lag_days
        FROM app_usage u
        LEFT JOIN app_list l ON u.application_name = l.app_name
        WHERE u.application_version != l.current_version 
        AND l.current_version IS NOT NULL
        """
        
        # Build filters
        filters = {}
        if app_name:
            filters['u.application_name'] = app_name
        
        # Map sort fields to actual column names
        sort_field_mapping = {
            'usage_sessions': 'usage_sessions',
            'version_lag_days': 'version_lag_days',
            'unique_users': 'unique_users',
            'total_hours': 'total_seconds'
        }
        
        actual_sort_field = sort_field_mapping[sort_by]
        order_clause = f"{actual_sort_field} {sort_order.upper()}"
        
        query, params = build_query(
            base_query=base_query,
            filters=filters,
            group_by="u.application_name, u.application_version",
            order_by=order_clause,
            limit=limit
        )
        
        if ctx:
            ctx.debug("Executing outdated versions query")
            ctx.report_progress(25, 100, "Querying outdated version data...")
        
        result = execute_analytics_query(query, params)
        
        if ctx:
            ctx.info(f"Retrieved {len(result.data)} outdated version records in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing outdated version analysis...")
        
        # Format response
        response_data = {
            "tool": "outdated_versions",
            "description": "Outdated application version analysis",
            "query_time_ms": result.query_time_ms,
            "total_outdated_records": result.total_count,
            "filters_applied": {
                "app_name": app_name,
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "outdated_versions": []
        }
        
        # Process outdated version data
        total_outdated_sessions = 0
        total_outdated_hours = 0
        unique_apps = set()
        critical_outdated = 0  # Versions more than 365 days old
        moderate_outdated = 0  # Versions 90-365 days old
        recent_outdated = 0    # Versions less than 90 days old
        
        for record in result.data:
            total_seconds = record["total_seconds"] or 0
            total_hours_for_version = total_seconds / 3600
            avg_session_minutes = (record["avg_session_seconds"] or 0) / 60
            version_lag_days = record["version_lag_days"] or 0
            
            total_outdated_sessions += record["usage_sessions"]
            total_outdated_hours += total_hours_for_version
            unique_apps.add(record["application_name"])
            
            # Categorize by severity
            if version_lag_days > 365:
                critical_outdated += 1
                severity = "critical"
            elif version_lag_days > 90:
                moderate_outdated += 1
                severity = "moderate"
            else:
                recent_outdated += 1
                severity = "low"
            
            # Generate recommendations
            recommendations = []
            if version_lag_days > 365:
                recommendations.append("Immediate update recommended - version is over 1 year old")
            elif version_lag_days > 180:
                recommendations.append("Update recommended - version is over 6 months old")
            elif record["usage_sessions"] > 100:
                recommendations.append("High usage detected - consider prioritizing update")
            
            if record["unique_users"] > 10:
                recommendations.append(f"Affects {record['unique_users']} users")
            
            version_info = {
                "application_name": record["application_name"],
                "outdated_version": record["application_version"],
                "current_version": record["current_version"],
                "app_type": record["app_type"],
                "publisher": record["publisher"],
                "version_analysis": {
                    "lag_days": version_lag_days,
                    "severity": severity,
                    "current_version_release_date": record["current_version_release_date"]
                },
                "usage_statistics": {
                    "sessions": record["usage_sessions"],
                    "unique_users": record["unique_users"],
                    "total_hours": round(total_hours_for_version, 2),
                    "average_session_minutes": round(avg_session_minutes, 2),
                    "first_usage_date": record["first_usage_date"],
                    "last_usage_date": record["last_usage_date"]
                },
                "recommendations": recommendations
            }
            response_data["outdated_versions"].append(version_info)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_outdated_sessions": total_outdated_sessions,
            "total_outdated_hours": round(total_outdated_hours, 2),
            "unique_applications_with_outdated_versions": len(unique_apps),
            "outdated_records_analyzed": len(result.data),
            "severity_breakdown": {
                "critical": critical_outdated,
                "moderate": moderate_outdated,
                "low": recent_outdated
            },
            "update_priority": {
                "high_priority": critical_outdated + moderate_outdated,
                "low_priority": recent_outdated
            }
        }
        
        # Add insights and recommendations
        response_data["insights"] = {
            "most_critical_apps": [
                app["application_name"] for app in response_data["outdated_versions"]
                if app["version_analysis"]["severity"] == "critical"
            ][:5],
            "highest_usage_outdated": [
                {
                    "app": app["application_name"],
                    "version": app["outdated_version"],
                    "sessions": app["usage_statistics"]["sessions"]
                }
                for app in sorted(response_data["outdated_versions"], 
                                key=lambda x: x["usage_statistics"]["sessions"], reverse=True)
            ][:5],
            "update_recommendations": {
                "immediate_action_needed": critical_outdated > 0,
                "total_apps_needing_updates": len(unique_apps),
                "estimated_users_affected": sum(app["usage_statistics"]["unique_users"] 
                                              for app in response_data["outdated_versions"])
            }
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Outdated versions analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} outdated versions, {critical_outdated} critical, {moderate_outdated} moderate")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in outdated_versions: {e}")
        if ctx:
            ctx.error(f"Failed to analyze outdated versions: {e}")
        
        return {
            "tool": "outdated_versions",
            "error": str(e),
            "message": "Failed to analyze outdated versions"
        }
