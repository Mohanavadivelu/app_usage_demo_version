"""
Tool: Heavy Users
Category: Advanced
Feature ID: 39

Description:
    Identify users with high usage

Parameters:
    - limit (int, optional): Maximum number of results to return

Returns:
    - Analytics results based on the specific tool functionality

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from mcp.types import Tool, TextContent
from typing import Dict, Any
import json
import logging

from shared.database_utils import execute_analytics_query, validate_parameters

logger = logging.getLogger(__name__)


async def heavy_users_handler(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the heavy_users tool request."""
    try:
        validated_params = validate_parameters(
            arguments,
            required=set(),
            optional={'limit'}
        )
        
        limit = validated_params.get('limit', 100)
        
        # TODO: Implement specific query logic for heavy_users
        query = "SELECT 1 as placeholder"
        result = execute_analytics_query(query, ())
        
        response_data = {
            "tool": "heavy_users",
            "description": "Identify users with high usage",
            "message": "Tool implementation in progress",
            "feature_id": 39
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in heavy_users_handler: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "tool": "heavy_users",
                "error": str(e),
                "message": "Failed to execute heavy_users"
            }, indent=2)
        )]


heavy_users_tool = Tool(
    name="heavy_users",
    description="Identify users with high usage",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            }
        },
        "additionalProperties": False
    }
)

heavy_users_tool.handler = heavy_users_handler
