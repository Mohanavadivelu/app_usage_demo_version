"""
Time Based tools for MCP App Usage Analytics Server.

This module implements time based tools corresponding to features 22-28.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

from .new_users_count import new_users_count_tool
from .active_users_count import active_users_count_tool
from .daily_usage_trend import daily_usage_trend_tool
from .usage_trends import usage_trends_tool
from .peak_usage_hours import peak_usage_hours_tool
from .onboarding_trend import onboarding_trend_tool
from .usage_comparison import usage_comparison_tool

logger = logging.getLogger(__name__)


def register_time_based_tools(server: Server) -> List[str]:
    """Register all time based tools with the MCP server."""
    registered_tools = []
    
    try:
        server.register_tool(new_users_count_tool)
        registered_tools.append("new_users_count")
        server.register_tool(active_users_count_tool)
        registered_tools.append("active_users_count")
        server.register_tool(daily_usage_trend_tool)
        registered_tools.append("daily_usage_trend")
        server.register_tool(usage_trends_tool)
        registered_tools.append("usage_trends")
        server.register_tool(peak_usage_hours_tool)
        registered_tools.append("peak_usage_hours")
        server.register_tool(onboarding_trend_tool)
        registered_tools.append("onboarding_trend")
        server.register_tool(usage_comparison_tool)
        registered_tools.append("usage_comparison")
        
        logger.info(f"Successfully registered {len(registered_tools)} time based tools")
        
    except Exception as e:
        logger.error(f"Error registering time based tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    'register_time_based_tools',
    'new_users_count_tool',
    'active_users_count_tool',
    'daily_usage_trend_tool',
    'usage_trends_tool',
    'peak_usage_hours_tool',
    'onboarding_trend_tool',
    'usage_comparison_tool'
]
