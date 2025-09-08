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

# Import all tool implementations - they will auto-register via @mcp.tool() decorators
from .list_applications import *
from .app_details import *
from .tracking_status import *
from .legacy_apps import *
from .recent_releases import *
from .top_publishers import *
from .app_versions import *
