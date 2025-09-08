"""
Version Tracking tools for MCP App Usage Analytics Server.

This module implements version tracking tools corresponding to features 33-36
from the requirements:

33. Usage statistics by application version
34. Compare legacy vs modern application versions
35. Identify outdated application versions
36. Version distribution analysis

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

# Import all tool implementations - they will auto-register via @mcp.tool() decorators
from .version_usage_breakdown import *
from .legacy_vs_modern import *
from .outdated_versions import *
from .version_distribution import *
