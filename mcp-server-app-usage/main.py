"""
MCP App Usage Analytics Server

This is the main entry point for the Model Context Protocol (MCP) server
that provides comprehensive analytics for application usage data.

The server implements 43 different analytics tools organized into categories:
- General: Basic app listing and information
- Usage Statistics: Usage time and user count analytics
- User-Centric: User-focused queries and statistics
- Time-Based: Time series and trend analysis
- Cross-Analysis: User-app relationship analysis
- Version Tracking: Version and legacy app analytics
- Advanced: Complex analytics and insights

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# Import configuration
from config.settings import get_settings, setup_logging
from config.database import get_default_config

# Import all tool categories
from general.tools import register_general_tools
from usage_stats.tools import register_usage_stats_tools
from user_centric.tools import register_user_centric_tools
from time_based.tools import register_time_based_tools
from cross_analysis.tools import register_cross_analysis_tools
from version_tracking.tools import register_version_tracking_tools
from advanced.tools import register_advanced_tools

# Initialize logging
logger = logging.getLogger(__name__)

# Create MCP server instance
app = Server("app-usage-analytics")


async def main():
    """
    Main entry point for the MCP server.
    
    This function initializes the server, registers all tools,
    and starts the stdio server for MCP communication.
    """
    try:
        # Load settings and setup logging
        settings = get_settings()
        setup_logging(settings)
        
        logger.info("Starting MCP App Usage Analytics Server")
        logger.info(f"Server settings: {settings.to_dict()}")
        
        # Validate database connection
        try:
            db_config = get_default_config()
            logger.info(f"Database path: {db_config.db_path}")
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            raise
        
        # Register all tool categories
        logger.info("Registering MCP tools...")
        
        # General tools (Features 1-7)
        general_tools = register_general_tools(app)
        logger.info(f"Registered {len(general_tools)} general tools")
        
        # Usage statistics tools (Features 8-14)
        usage_stats_tools = register_usage_stats_tools(app)
        logger.info(f"Registered {len(usage_stats_tools)} usage statistics tools")
        
        # User-centric tools (Features 15-21)
        user_centric_tools = register_user_centric_tools(app)
        logger.info(f"Registered {len(user_centric_tools)} user-centric tools")
        
        # Time-based tools (Features 22-28)
        time_based_tools = register_time_based_tools(app)
        logger.info(f"Registered {len(time_based_tools)} time-based tools")
        
        # Cross-analysis tools (Features 29-32)
        cross_analysis_tools = register_cross_analysis_tools(app)
        logger.info(f"Registered {len(cross_analysis_tools)} cross-analysis tools")
        
        # Version tracking tools (Features 33-36)
        version_tracking_tools = register_version_tracking_tools(app)
        logger.info(f"Registered {len(version_tracking_tools)} version tracking tools")
        
        # Advanced analytics tools (Features 37-43)
        advanced_tools = register_advanced_tools(app)
        logger.info(f"Registered {len(advanced_tools)} advanced analytics tools")
        
        # Calculate total tools
        total_tools = (
            len(general_tools) + len(usage_stats_tools) + len(user_centric_tools) +
            len(time_based_tools) + len(cross_analysis_tools) + 
            len(version_tracking_tools) + len(advanced_tools)
        )
        
        logger.info(f"Successfully registered {total_tools} MCP tools across 7 categories")
        
        # Start the stdio server
        logger.info("Starting MCP stdio server...")
        async with stdio_server() as streams:
            await app.run(
                streams[0], streams[1],
                app.create_initialization_options()
            )
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("MCP App Usage Analytics Server stopped")


if __name__ == "__main__":
    """
    Entry point when running the server directly.
    
    Usage:
        python main.py
    
    The server will start and listen for MCP protocol messages
    on stdin/stdout for communication with MCP clients.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)
