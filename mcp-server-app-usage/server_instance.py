"""
MCP Server Instance

Centralized FastMCP server instance to avoid circular imports.
All tools should import the mcp instance from this module.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.server.fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP("app-usage-analytics")
