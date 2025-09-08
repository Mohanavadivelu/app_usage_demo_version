"""
Usage Statistics tools for MCP App Usage Analytics Server.

This module implements usage statistics and analytics tools
corresponding to features 8-14 from the requirements:

8. List applications and their total usage time (in hours)
9. Display the number of users using each application
10. Calculate the average time spent per user per application
11. Rank applications by total usage time (e.g., top 5, top 10)
12. Rank applications by the number of unique users
13. Calculate total usage time across all apps for a given day, week, or month
14. Identify which applications are used most on each platform

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

# Import individual tool implementations
from .usage_time_stats import usage_time_stats_tool
from .user_count_stats import user_count_stats_tool
from .average_usage_time import average_usage_time_tool
from .top_apps_by_usage import top_apps_by_usage_tool
from .top_apps_by_users import top_apps_by_users_tool
from .total_usage_period import total_usage_period_tool
from .platform_usage_stats import platform_usage_stats_tool

logger = logging.getLogger(__name__)


def register_usage_stats_tools(server: Server) -> List[str]:
    """Register all usage statistics tools with the MCP server."""
    registered_tools = []
    
    try:
        # Feature 8: List applications and their total usage time
        server.register_tool(usage_time_stats_tool)
        registered_tools.append("usage_time_stats")
        
        # Feature 9: Display the number of users using each application
        server.register_tool(user_count_stats_tool)
        registered_tools.append("user_count_stats")
        
        # Feature 10: Calculate average time spent per user per application
        server.register_tool(average_usage_time_tool)
        registered_tools.append("average_usage_time")
        
        # Feature 11: Rank applications by total usage time
        server.register_tool(top_apps_by_usage_tool)
        registered_tools.append("top_apps_by_usage")
        
        # Feature 12: Rank applications by number of unique users
        server.register_tool(top_apps_by_users_tool)
        registered_tools.append("top_apps_by_users")
        
        # Feature 13: Calculate total usage time for time periods
        server.register_tool(total_usage_period_tool)
        registered_tools.append("total_usage_period")
        
        # Feature 14: Applications used most on each platform
        server.register_tool(platform_usage_stats_tool)
        registered_tools.append("platform_usage_stats")
        
        logger.info(f"Successfully registered {len(registered_tools)} usage statistics tools")
        
    except Exception as e:
        logger.error(f"Error registering usage statistics tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    'register_usage_stats_tools',
    'usage_time_stats_tool',
    'user_count_stats_tool',
    'average_usage_time_tool',
    'top_apps_by_usage_tool',
    'top_apps_by_users_tool',
    'total_usage_period_tool',
    'platform_usage_stats_tool'
]
