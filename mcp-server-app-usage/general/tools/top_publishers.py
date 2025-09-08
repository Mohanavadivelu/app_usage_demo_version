"""
Tool: Top Publishers
Category: General
Feature ID: 6

Description:
    Show publishers who have released the most applications.

Parameters:
    - top_n (int, optional): Number of top publishers to return
    - include_app_details (bool, optional): Include list of apps per publisher

Returns:
    - Ranked list of publishers by application count

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from typing import Optional, Dict, Any
import logging

from mcp.server.fastmcp import Context
from shared.database_utils import execute_analytics_query

logger = logging.getLogger(__name__)

# Import the mcp instance from main module
from main import mcp


@mcp.tool()
async def top_publishers(
    top_n: int = 10,
    include_app_details: bool = False,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Show publishers who have released the most applications.
    
    Args:
        top_n: Number of top publishers to return (default: 10, max: 100)
        include_app_details: Include list of applications per publisher (default: false)
        ctx: FastMCP context for logging and progress reporting
    
    Returns:
        Dictionary containing ranked list of publishers by application count
    """
    try:
        if ctx:
            ctx.info(f"Finding top {top_n} publishers, include_app_details: {include_app_details}")
        
        # Validate parameters
        if top_n < 1 or top_n > 100:
            raise ValueError("top_n must be between 1 and 100")
        
        # Get publisher rankings
        query = """
        SELECT 
            publisher,
            COUNT(*) as app_count,
            COUNT(CASE WHEN enable_tracking = 1 THEN 1 END) as tracking_enabled_count,
            GROUP_CONCAT(DISTINCT app_type) as app_types
        FROM app_list
        GROUP BY publisher
        ORDER BY app_count DESC
        LIMIT ?
        """
        
        if ctx:
            ctx.debug("Executing top publishers query")
            ctx.report_progress(25, 100, "Querying publisher rankings...")
        
        result = execute_analytics_query(query, (top_n,))
        
        if ctx:
            ctx.info(f"Found {len(result.data)} publishers in {result.query_time_ms}ms")
            ctx.report_progress(50, 100, "Processing publisher data...")
        
        response_data = {
            "tool": "top_publishers",
            "description": f"Top {top_n} publishers by application count",
            "query_time_ms": result.query_time_ms,
            "total_publishers": result.total_count,
            "include_app_details": include_app_details,
            "publishers": []
        }
        
        total_apps = 0
        total_tracking_enabled = 0
        
        for i, publisher in enumerate(result.data, 1):
            total_apps += publisher["app_count"]
            total_tracking_enabled += publisher["tracking_enabled_count"]
            
            publisher_info = {
                "rank": i,
                "publisher": publisher["publisher"],
                "total_applications": publisher["app_count"],
                "tracking_enabled": publisher["tracking_enabled_count"],
                "tracking_disabled": publisher["app_count"] - publisher["tracking_enabled_count"],
                "tracking_percentage": round((publisher["tracking_enabled_count"] / publisher["app_count"] * 100), 2),
                "app_types": publisher["app_types"].split(",") if publisher["app_types"] else [],
                "unique_app_types": len(publisher["app_types"].split(",")) if publisher["app_types"] else 0
            }
            
            # Add app details if requested
            if include_app_details:
                if ctx:
                    ctx.debug(f"Fetching app details for publisher: {publisher['publisher']}")
                
                app_query = """
                SELECT app_name, app_type, current_version, released_date, enable_tracking
                FROM app_list
                WHERE publisher = ?
                ORDER BY released_date DESC
                """
                app_result = execute_analytics_query(app_query, (publisher["publisher"],))
                publisher_info["applications"] = [
                    {
                        "name": app["app_name"],
                        "type": app["app_type"],
                        "version": app["current_version"],
                        "released_date": app["released_date"],
                        "tracking_enabled": bool(app["enable_tracking"])
                    }
                    for app in app_result.data
                ]
                
                if ctx:
                    ctx.debug(f"Added {len(app_result.data)} apps for {publisher['publisher']}")
            
            response_data["publishers"].append(publisher_info)
        
        # Add summary statistics
        response_data["summary"] = {
            "total_apps_from_top_publishers": total_apps,
            "total_tracking_enabled": total_tracking_enabled,
            "overall_tracking_percentage": round((total_tracking_enabled / total_apps * 100), 2) if total_apps > 0 else 0,
            "average_apps_per_publisher": round(total_apps / len(result.data), 2) if result.data else 0
        }
        
        if ctx:
            ctx.report_progress(100, 100, "Top publishers analysis complete")
            ctx.info(f"Analysis complete: {len(result.data)} publishers with {total_apps} total apps")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in top_publishers: {e}")
        if ctx:
            ctx.error(f"Failed to retrieve top publishers: {e}")
        
        return {
            "tool": "top_publishers",
            "error": str(e),
            "message": "Failed to retrieve top publishers"
        }
