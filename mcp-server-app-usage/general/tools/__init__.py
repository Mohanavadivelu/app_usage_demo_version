"""
General tools for MCP App Usage Analytics Server.

This module implements basic application listing and information tools
corresponding to features 1-7 from the requirements:

1. List all applications being tracked
2. Show details of an application
3. Identify which applications have tracking enabled
4. List legacy applications
5. List applications released in the last X days or months
6. Show publishers who have released the most applications
7. List applications along with their current version

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List, Dict, Any
import logging

# Import individual tool implementations
from .list_applications import list_applications_tool
from .app_details import app_details_tool
from .tracking_status import tracking_status_tool
from .legacy_apps import legacy_apps_tool
from .recent_releases import recent_releases_tool
from .top_publishers import top_publishers_tool
from .app_versions import app_versions_tool

logger = logging.getLogger(__name__)


def register_general_tools(server: Server) -> List[str]:
    """
    Register all general tools with the MCP server.
    
    This function registers all 7 general tools that provide basic
    application information and listing capabilities.
    
    Args:
        server (Server): MCP server instance
    
    Returns:
        list: List of registered tool names
    
    Example:
        >>> from mcp.server import Server
        >>> server = Server("test")
        >>> tools = register_general_tools(server)
        >>> print(f"Registered {len(tools)} general tools")
        Registered 7 general tools
    """
    registered_tools = []
    
    try:
        # Feature 1: List all applications being tracked
        server.register_tool(list_applications_tool)
        registered_tools.append("list_applications")
        logger.debug("Registered list_applications tool")
        
        # Feature 2: Show details of an application
        server.register_tool(app_details_tool)
        registered_tools.append("app_details")
        logger.debug("Registered app_details tool")
        
        # Feature 3: Identify which applications have tracking enabled
        server.register_tool(tracking_status_tool)
        registered_tools.append("tracking_status")
        logger.debug("Registered tracking_status tool")
        
        # Feature 4: List legacy applications
        server.register_tool(legacy_apps_tool)
        registered_tools.append("legacy_apps")
        logger.debug("Registered legacy_apps tool")
        
        # Feature 5: List applications released in the last X days or months
        server.register_tool(recent_releases_tool)
        registered_tools.append("recent_releases")
        logger.debug("Registered recent_releases tool")
        
        # Feature 6: Show publishers who have released the most applications
        server.register_tool(top_publishers_tool)
        registered_tools.append("top_publishers")
        logger.debug("Registered top_publishers tool")
        
        # Feature 7: List applications along with their current version
        server.register_tool(app_versions_tool)
        registered_tools.append("app_versions")
        logger.debug("Registered app_versions tool")
        
        logger.info(f"Successfully registered {len(registered_tools)} general tools")
        
    except Exception as e:
        logger.error(f"Error registering general tools: {e}")
        raise
    
    return registered_tools


# Export all tools for direct access if needed
__all__ = [
    'register_general_tools',
    'list_applications_tool',
    'app_details_tool',
    'tracking_status_tool',
    'legacy_apps_tool',
    'recent_releases_tool',
    'top_publishers_tool',
    'app_versions_tool'
]
