"""
Advanced tools for MCP App Usage Analytics Server.

This module implements advanced tools corresponding to features 37-43.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

from .session_length_analysis import session_length_analysis_tool
from .median_session_length import median_session_length_tool
from .heavy_users import heavy_users_tool
from .inactive_users import inactive_users_tool
from .churn_rate_analysis import churn_rate_analysis_tool
from .new_vs_returning_users import new_vs_returning_users_tool
from .growth_trend_analysis import growth_trend_analysis_tool

logger = logging.getLogger(__name__)


def register_advanced_tools(server: Server) -> List[str]:
    """Register all advanced tools with the MCP server."""
    registered_tools = []
    
    try:
        server.register_tool(session_length_analysis_tool)
        registered_tools.append("session_length_analysis")
        server.register_tool(median_session_length_tool)
        registered_tools.append("median_session_length")
        server.register_tool(heavy_users_tool)
        registered_tools.append("heavy_users")
        server.register_tool(inactive_users_tool)
        registered_tools.append("inactive_users")
        server.register_tool(churn_rate_analysis_tool)
        registered_tools.append("churn_rate_analysis")
        server.register_tool(new_vs_returning_users_tool)
        registered_tools.append("new_vs_returning_users")
        server.register_tool(growth_trend_analysis_tool)
        registered_tools.append("growth_trend_analysis")
        
        logger.info(f"Successfully registered {len(registered_tools)} advanced tools")
        
    except Exception as e:
        logger.error(f"Error registering advanced tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    'register_advanced_tools',
    'session_length_analysis_tool',
    'median_session_length_tool',
    'heavy_users_tool',
    'inactive_users_tool',
    'churn_rate_analysis_tool',
    'new_vs_returning_users_tool',
    'growth_trend_analysis_tool'
]
