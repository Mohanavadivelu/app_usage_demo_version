"""
Cross Analysis Tools Package

This package contains tools for cross-analysis of user and application data:
- user_app_matrix: Cross-tab display of users vs applications matrix
- multi_app_users: Calculate users who use multiple applications  
- common_app_combinations: Identify applications commonly used together
- user_app_usage_percentage: Calculate percentage of total usage time per application per user

Author: MCP App Usage Analytics Team
Created: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

from .user_app_matrix import user_app_matrix_tool
from .multi_app_users import multi_app_users_tool
from .common_app_combinations import common_app_combinations_tool
from .usage_percentage_breakdown import usage_percentage_breakdown_tool

logger = logging.getLogger(__name__)


def register_cross_analysis_tools(server: Server) -> List[str]:
    """Register all cross analysis tools with the MCP server."""
    registered_tools = []
    
    try:
        # Feature 29: Cross-tab display of users vs applications matrix
        server.register_tool(user_app_matrix_tool)
        registered_tools.append("user_app_matrix")
        
        # Feature 30: Calculate users who use multiple applications
        server.register_tool(multi_app_users_tool)
        registered_tools.append("multi_app_users")
        
        # Feature 31: Identify applications commonly used together
        server.register_tool(common_app_combinations_tool)
        registered_tools.append("common_app_combinations")
        
        # Feature 32: Calculate percentage of total usage time per application per user
        server.register_tool(usage_percentage_breakdown_tool)
        registered_tools.append("usage_percentage_breakdown")
        
        logger.info(f"Successfully registered {len(registered_tools)} cross analysis tools")
        
    except Exception as e:
        logger.error(f"Error registering cross analysis tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    "register_cross_analysis_tools",
    "user_app_matrix_tool",
    "multi_app_users_tool", 
    "common_app_combinations_tool",
    "usage_percentage_breakdown_tool"
]
