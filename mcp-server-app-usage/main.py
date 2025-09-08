"""
MCP App Usage Analytics Server

This is the main entry point for the Model Context Protocol (MCP) server
that provides comprehensive analytics for application usage data.

The server implements general analytics tools for basic app listing and information.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import logging

# Import configuration
from config.settings import get_settings, setup_logging
from config.database import get_default_config

# Import the centralized MCP server instance
from server_instance import mcp

# Import general tools (they will auto-register via decorators)
import general.tools

# Import version tracking tools (they will auto-register via decorators)
import version_tracking.tools

# Initialize logging
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the MCP server.
    
    This function initializes the server and starts the stdio server for MCP communication.
    """
    try:
        # Load settings and setup logging
        settings = get_settings()
        setup_logging(settings)
        
        logger.info("Starting MCP App Usage Analytics Server (FastMCP)")
        logger.info(f"Server settings: {settings.to_dict()}")
        
        # Validate database connection
        try:
            db_config = get_default_config()
            logger.info(f"Database path: {db_config.db_path}")
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            raise
        
        logger.info("General tools loaded and registered via decorators")
        
        # Start the stdio server
        logger.info("Starting FastMCP stdio server...")
        mcp.run(transport="stdio")
            
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
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)
