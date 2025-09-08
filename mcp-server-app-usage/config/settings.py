"""
Server settings and configuration for MCP App Usage Analytics Server.

This module manages server-wide settings, logging configuration,
and application parameters.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ServerSettings:
    """
    Server configuration settings.
    
    This class contains all configurable parameters for the MCP server,
    including logging levels, performance settings, and feature flags.
    
    Attributes:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        max_query_results (int): Maximum number of results to return per query
        cache_enabled (bool): Whether to enable query result caching
        cache_ttl (int): Cache time-to-live in seconds
        date_format (str): Default date format for date parsing
        timezone (str): Default timezone for date operations
    """
    
    log_level: str = "INFO"
    max_query_results: int = 1000
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    date_format: str = "%Y-%m-%d"
    timezone: str = "UTC"
    
    # Performance settings
    query_timeout: int = 30
    connection_pool_size: int = 10
    
    # Feature flags
    enable_advanced_analytics: bool = True
    enable_real_time_updates: bool = False
    enable_data_export: bool = True
    
    # Security settings
    enable_authentication: bool = False
    api_key_required: bool = False
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100
    
    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate_settings()
    
    def _validate_settings(self):
        """
        Validate configuration settings.
        
        Raises:
            ValueError: If any setting is invalid
        """
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        if self.max_query_results <= 0:
            raise ValueError("max_query_results must be positive")
        
        if self.cache_ttl < 0:
            raise ValueError("cache_ttl must be non-negative")
        
        if self.query_timeout <= 0:
            raise ValueError("query_timeout must be positive")
        
        if self.connection_pool_size <= 0:
            raise ValueError("connection_pool_size must be positive")
        
        if self.max_requests_per_minute <= 0:
            raise ValueError("max_requests_per_minute must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary.
        
        Returns:
            dict: Settings as key-value pairs
        """
        return {
            'log_level': self.log_level,
            'max_query_results': self.max_query_results,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'date_format': self.date_format,
            'timezone': self.timezone,
            'query_timeout': self.query_timeout,
            'connection_pool_size': self.connection_pool_size,
            'enable_advanced_analytics': self.enable_advanced_analytics,
            'enable_real_time_updates': self.enable_real_time_updates,
            'enable_data_export': self.enable_data_export,
            'enable_authentication': self.enable_authentication,
            'api_key_required': self.api_key_required,
            'rate_limit_enabled': self.rate_limit_enabled,
            'max_requests_per_minute': self.max_requests_per_minute
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ServerSettings':
        """
        Create settings from dictionary.
        
        Args:
            config_dict (dict): Configuration dictionary
        
        Returns:
            ServerSettings: Settings instance
        """
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> 'ServerSettings':
        """
        Create settings from environment variables.
        
        Environment variables should be prefixed with 'MCP_APP_USAGE_'
        
        Returns:
            ServerSettings: Settings instance with values from environment
        """
        env_mapping = {
            'MCP_APP_USAGE_LOG_LEVEL': 'log_level',
            'MCP_APP_USAGE_MAX_QUERY_RESULTS': 'max_query_results',
            'MCP_APP_USAGE_CACHE_ENABLED': 'cache_enabled',
            'MCP_APP_USAGE_CACHE_TTL': 'cache_ttl',
            'MCP_APP_USAGE_DATE_FORMAT': 'date_format',
            'MCP_APP_USAGE_TIMEZONE': 'timezone',
            'MCP_APP_USAGE_QUERY_TIMEOUT': 'query_timeout',
            'MCP_APP_USAGE_CONNECTION_POOL_SIZE': 'connection_pool_size',
            'MCP_APP_USAGE_ENABLE_ADVANCED_ANALYTICS': 'enable_advanced_analytics',
            'MCP_APP_USAGE_ENABLE_REAL_TIME_UPDATES': 'enable_real_time_updates',
            'MCP_APP_USAGE_ENABLE_DATA_EXPORT': 'enable_data_export',
            'MCP_APP_USAGE_ENABLE_AUTHENTICATION': 'enable_authentication',
            'MCP_APP_USAGE_API_KEY_REQUIRED': 'api_key_required',
            'MCP_APP_USAGE_RATE_LIMIT_ENABLED': 'rate_limit_enabled',
            'MCP_APP_USAGE_MAX_REQUESTS_PER_MINUTE': 'max_requests_per_minute'
        }
        
        config_dict = {}
        for env_var, setting_name in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if setting_name in ['max_query_results', 'cache_ttl', 'query_timeout', 
                                  'connection_pool_size', 'max_requests_per_minute']:
                    config_dict[setting_name] = int(value)
                elif setting_name in ['cache_enabled', 'enable_advanced_analytics', 
                                    'enable_real_time_updates', 'enable_data_export',
                                    'enable_authentication', 'api_key_required', 'rate_limit_enabled']:
                    config_dict[setting_name] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    config_dict[setting_name] = value
        
        return cls(**config_dict)


def setup_logging(settings: ServerSettings):
    """
    Configure logging based on server settings.
    
    Args:
        settings (ServerSettings): Server configuration
    """
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific logger levels
    logging.getLogger('mcp').setLevel(getattr(logging, settings.log_level))
    logging.getLogger('sqlite3').setLevel(logging.WARNING)  # Reduce SQLite noise


# Global settings instance
_settings = None


def get_settings() -> ServerSettings:
    """
    Get the global server settings instance.
    
    Returns:
        ServerSettings: Global settings instance
    """
    global _settings
    if _settings is None:
        _settings = ServerSettings.from_env()
    return _settings


def set_settings(settings: ServerSettings):
    """
    Set the global server settings.
    
    Args:
        settings (ServerSettings): Settings to set as global
    """
    global _settings
    _settings = settings


def load_settings_from_file(file_path: str) -> ServerSettings:
    """
    Load settings from a configuration file.
    
    Args:
        file_path (str): Path to configuration file (JSON format)
    
    Returns:
        ServerSettings: Settings loaded from file
    
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If configuration file is invalid
    """
    import json
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return ServerSettings.from_dict(config_dict)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration file: {e}")


def save_settings_to_file(settings: ServerSettings, file_path: str):
    """
    Save settings to a configuration file.
    
    Args:
        settings (ServerSettings): Settings to save
        file_path (str): Path to save configuration file
    """
    import json
    
    with open(file_path, 'w') as f:
        json.dump(settings.to_dict(), f, indent=2)
