"""
User Centric tools for MCP App Usage Analytics Server.

This module implements user centric tools corresponding to features 15-21.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

from .user_applications import user_applications_tool
from .user_total_hours import user_total_hours_tool
from .user_app_hours import user_app_hours_tool
from .user_last_app import user_last_app_tool
from .user_last_active import user_last_active_tool
from .user_top_apps import user_top_apps_tool
from .app_users import app_users_tool

logger = logging.getLogger(__name__)


def register_user_centric_tools(server: Server) -> List[str]:
    """Register all user centric tools with the MCP server."""
    registered_tools = []
    
    try:
        server.register_tool(user_applications_tool)
        registered_tools.append("user_applications")
        server.register_tool(user_total_hours_tool)
        registered_tools.append("user_total_hours")
        server.register_tool(user_app_hours_tool)
        registered_tools.append("user_app_hours")
        server.register_tool(user_last_app_tool)
        registered_tools.append("user_last_app")
        server.register_tool(user_last_active_tool)
        registered_tools.append("user_last_active")
        server.register_tool(user_top_apps_tool)
        registered_tools.append("user_top_apps")
        server.register_tool(app_users_tool)
        registered_tools.append("app_users")
        
        logger.info(f"Successfully registered {len(registered_tools)} user centric tools")
        
    except Exception as e:
        logger.error(f"Error registering user centric tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    'register_user_centric_tools',
    'user_applications_tool',
    'user_total_hours_tool',
    'user_app_hours_tool',
    'user_last_app_tool',
    'user_last_active_tool',
    'user_top_apps_tool',
    'app_users_tool'
]
