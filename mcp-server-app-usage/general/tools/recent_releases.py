"""
Tool: Recent Releases
Category: General
Feature ID: 5

Description:
    List applications released in the last X days or months.

Parameters:
    - days (int, optional): Number of days to look back
    - months (int, optional): Number of months to look back
    - limit (int, optional): Maximum number of results

Returns:
    - List of recently released applications

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query
from shared.date_utils import days_ago

logger = logging.getLogger(__name__)

# Import the mcp instance from main module
from main import mcp


@mcp.tool()
async def recent_releases(
    days: Optional[int] = None,
    months: Optional[int] = None,
    limit: int = 100,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    List applications released in the last X days or months.
    
    Args:
        days: Number of days to look back (1-365)
        months: Number of months to look back (1-12)
        limit: Maximum number of applications to return (default: 100, max: 1000)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing recently released applications
    """
    try:
        if ctx:
            period_desc = f"{days} days" if days else f"{months} months" if months else "30 days (default)"
            ctx.info(f"Finding applications released in the last {period_desc}, limit: {limit}")
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        
        if days and (days < 1 or days > 365):
            raise ValueError("days must be between 1 and 365")
        
        if months and (months < 1 or months > 12):
            raise ValueError("months must be between 1 and 12")
        
        if days and months:
            raise ValueError("Cannot specify both days and months")
        
        # Calculate cutoff date
        if days:
            cutoff_date = days_ago(days)
            period_description = f"{days} days"
        elif months:
            cutoff_date = days_ago(months * 30)  # Approximate
            period_description = f"{months} months"
        else:
            cutoff_date = days_ago(30)  # Default to 30 days
            period_description = "30 days (default)"
        
        if ctx:
            ctx.debug(f"Using cutoff date: {cutoff_date}")
            ctx.report_progress(25, 100, "Querying recent releases...")
        
        query = """
        SELECT 
            app_name, app_type, current_version, released_date,
            publisher, description, enable_tracking
        FROM app_list
        WHERE released_date >= ?
        ORDER BY released_date DESC
        LIMIT ?
        """
        
        result = execute_analytics_query(query, (cutoff_date, limit))
        
        if ctx:
            ctx.info(f"Found {len(result.data)} recent releases in {result.query_time_ms}ms")
            ctx.report_progress(75, 100, "Processing release data...")
        
        response_data = {
            "tool": "recent_releases",
            "description": f"Applications released in the last {period_description}",
            "query_time_ms": result.query_time_ms,
            "cutoff_date": cutoff_date,
            "period": period_description,
            "total_recent_releases": result.total_count,
            "limit_applied": limit,
            "recent_applications": []
        }
        
        publishers = {}
        app_types = {}
        
        for app in result.data:
            app_info = {
                "name": app["app_name"],
                "type": app["app_type"],
                "version": app["current_version"],
                "released_date": app["released_date"],
                "publisher": app["publisher"],
                "description": app["description"][:100] + "..." if len(app["description"]) > 100 else app["description"],
                "tracking_enabled": bool(app["enable_tracking"])
            }
            response_data["recent_applications"].append(app_info)
            
            # Count by publisher and type
            publishers[app["publisher"]] = publishers.get(app["publisher"], 0) + 1
            app_types[app["app_type"]] = app_types.get(app["app_type"], 0) + 1
        
        response_data["summary"] = {
            "total_releases": len(result.data),
            "unique_publishers": len(publishers),
            "unique_app_types": len(app_types),
            "top_publishers": sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:5],
            "app_types_breakdown": sorted(app_types.items(), key=lambda x: x[1], reverse=True)
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Recent releases analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} releases from {len(publishers)} publishers")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in recent_releases: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve recent releases: {e}")
        
        return {
            "tool": "recent_releases",
            "error": str(e),
            "message": "Failed to retrieve recent releases"
        }
