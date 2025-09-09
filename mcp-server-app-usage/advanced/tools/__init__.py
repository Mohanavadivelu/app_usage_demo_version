"""
Advanced tools for MCP App Usage Analytics Server.

This module implements advanced tools corresponding to features 37-43.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

# Import all tool implementations - they will auto-register via @mcp.tool() decorators
from .churn_rate_analysis import *
from .growth_trend_analysis import *
from .heavy_users import *
from .inactive_users import *
from .median_session_length import *
from .new_vs_returning_users import *
from .session_length_analysis import *
