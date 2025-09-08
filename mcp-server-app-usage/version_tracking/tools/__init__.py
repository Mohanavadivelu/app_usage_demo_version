"""
Version Tracking tools for MCP App Usage Analytics Server.

This module implements version tracking tools corresponding to features 33-36.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server import Server
from typing import List
import logging

from .version_usage_breakdown import version_usage_breakdown_tool
from .legacy_vs_modern import legacy_vs_modern_tool
from .outdated_versions import outdated_versions_tool
from .version_distribution import version_distribution_tool

logger = logging.getLogger(__name__)


def register_version_tracking_tools(server: Server) -> List[str]:
    """Register all version tracking tools with the MCP server."""
    registered_tools = []
    
    try:
        server.register_tool(version_usage_breakdown_tool)
        registered_tools.append("version_usage_breakdown")
        server.register_tool(legacy_vs_modern_tool)
        registered_tools.append("legacy_vs_modern")
        server.register_tool(outdated_versions_tool)
        registered_tools.append("outdated_versions")
        server.register_tool(version_distribution_tool)
        registered_tools.append("version_distribution")
        
        logger.info(f"Successfully registered {len(registered_tools)} version tracking tools")
        
    except Exception as e:
        logger.error(f"Error registering version tracking tools: {e}")
        raise
    
    return registered_tools


__all__ = [
    'register_version_tracking_tools',
    'version_usage_breakdown_tool',
    'legacy_vs_modern_tool',
    'outdated_versions_tool',
    'version_distribution_tool'
]
