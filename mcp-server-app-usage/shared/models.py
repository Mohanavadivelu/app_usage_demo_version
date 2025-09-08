"""
Data models for MCP App Usage Analytics Server.

This module defines data structures used throughout the application
for representing database records, analytics results, and API responses.

Author: MCP App Usage Analytics Team
Created: 2025-01-08
Last Modified: 2025-01-08
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date


@dataclass
class AppUsageRecord:
    """
    Represents a single app usage record from the database.
    
    This model corresponds to the app_usage table structure and provides
    a typed interface for working with usage data.
    
    Attributes:
        id (int): Unique record identifier
        monitor_app_version (str): Version of the monitoring application
        platform (str): Platform where the app was used (Windows, Linux, etc.)
        user (str): Username or user identifier
        application_name (str): Name of the application used
        application_version (str): Version of the application used
        log_date (str): Date when usage was logged (YYYY-MM-DD format)
        legacy_app (bool): Whether the application is considered legacy
        duration_seconds (int): Usage duration in seconds
        created_at (datetime): When the record was created
        updated_at (datetime): When the record was last updated
    """
    
    id: int
    monitor_app_version: str
    platform: str
    user: str
    application_name: str
    application_version: str
    log_date: str
    legacy_app: bool
    duration_seconds: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration_seconds / 3600.0
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration_seconds / 60.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'monitor_app_version': self.monitor_app_version,
            'platform': self.platform,
            'user': self.user,
            'application_name': self.application_name,
            'application_version': self.application_version,
            'log_date': self.log_date,
            'legacy_app': self.legacy_app,
            'duration_seconds': self.duration_seconds,
            'duration_hours': self.duration_hours,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AppListRecord:
    """
    Represents an application record from the app_list table.
    
    This model corresponds to the app_list table structure and provides
    metadata about tracked applications.
    
    Attributes:
        app_id (int): Unique application identifier
        app_name (str): Name of the application
        app_type (str): Type/category of the application
        current_version (str): Current version of the application
        released_date (str): Release date (YYYY-MM-DD format)
        publisher (str): Application publisher/developer
        description (str): Application description
        download_link (str): Download URL for the application
        enable_tracking (bool): Whether tracking is enabled
        track_usage (bool): Whether usage tracking is enabled
        track_location (bool): Whether location tracking is enabled
        track_cm (bool): Whether CPU/memory tracking is enabled
        track_intr (int): Tracking interval in seconds
        registered_date (str): Date when app was registered (YYYY-MM-DD format)
    """
    
    app_id: int
    app_name: str
    app_type: str
    current_version: str
    released_date: str
    publisher: str
    description: str
    download_link: str
    enable_tracking: bool
    track_usage: bool
    track_location: bool
    track_cm: bool
    track_intr: int
    registered_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'app_type': self.app_type,
            'current_version': self.current_version,
            'released_date': self.released_date,
            'publisher': self.publisher,
            'description': self.description,
            'download_link': self.download_link,
            'enable_tracking': self.enable_tracking,
            'track_usage': self.track_usage,
            'track_location': self.track_location,
            'track_cm': self.track_cm,
            'track_intr': self.track_intr,
            'registered_date': self.registered_date
        }


@dataclass
class AnalyticsResult:
    """
    Generic container for analytics query results.
    
    This model provides a standardized way to return analytics data
    with metadata about the query and results.
    
    Attributes:
        data (List[Dict[str, Any]]): Query result data
        total_count (int): Total number of records
        query_time_ms (float): Query execution time in milliseconds
        metadata (Dict[str, Any]): Additional metadata about the query
    """
    
    data: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'data': self.data,
            'total_count': self.total_count,
            'query_time_ms': self.query_time_ms,
            'metadata': self.metadata
        }


@dataclass
class TimeSeriesData:
    """
    Represents time series data for trend analysis.
    
    This model is used for returning time-based analytics data
    such as daily usage trends, user growth, etc.
    
    Attributes:
        timestamps (List[str]): List of timestamps (dates or datetimes)
        values (List[Union[int, float]]): Corresponding values for each timestamp
        label (str): Label describing what the values represent
        unit (str): Unit of measurement for the values
    """
    
    timestamps: List[str]
    values: List[Union[int, float]]
    label: str
    unit: str = ""
    
    def __post_init__(self):
        """Validate that timestamps and values have the same length."""
        if len(self.timestamps) != len(self.values):
            raise ValueError("Timestamps and values must have the same length")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'timestamps': self.timestamps,
            'values': self.values,
            'label': self.label,
            'unit': self.unit,
            'data_points': len(self.timestamps)
        }


@dataclass
class UserStats:
    """
    Represents user-specific statistics.
    
    This model aggregates various statistics for a specific user
    across all applications and time periods.
    
    Attributes:
        user_id (str): User identifier
        total_usage_hours (float): Total usage time in hours
        total_applications (int): Number of unique applications used
        most_used_app (str): Name of most frequently used application
        last_active_date (str): Date of last activity
        average_daily_usage (float): Average daily usage in hours
        platform_breakdown (Dict[str, float]): Usage hours by platform
    """
    
    user_id: str
    total_usage_hours: float
    total_applications: int
    most_used_app: Optional[str] = None
    last_active_date: Optional[str] = None
    average_daily_usage: float = 0.0
    platform_breakdown: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.platform_breakdown is None:
            self.platform_breakdown = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'user_id': self.user_id,
            'total_usage_hours': round(self.total_usage_hours, 2),
            'total_applications': self.total_applications,
            'most_used_app': self.most_used_app,
            'last_active_date': self.last_active_date,
            'average_daily_usage': round(self.average_daily_usage, 2),
            'platform_breakdown': {k: round(v, 2) for k, v in self.platform_breakdown.items()}
        }


@dataclass
class AppStats:
    """
    Represents application-specific statistics.
    
    This model aggregates various statistics for a specific application
    across all users and time periods.
    
    Attributes:
        app_name (str): Application name
        total_usage_hours (float): Total usage time across all users
        unique_users (int): Number of unique users
        average_session_duration (float): Average session duration in minutes
        most_active_user (str): User with highest usage
        version_breakdown (Dict[str, float]): Usage hours by version
        platform_breakdown (Dict[str, int]): User count by platform
    """
    
    app_name: str
    total_usage_hours: float
    unique_users: int
    average_session_duration: float = 0.0
    most_active_user: Optional[str] = None
    version_breakdown: Optional[Dict[str, float]] = None
    platform_breakdown: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.version_breakdown is None:
            self.version_breakdown = {}
        if self.platform_breakdown is None:
            self.platform_breakdown = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'app_name': self.app_name,
            'total_usage_hours': round(self.total_usage_hours, 2),
            'unique_users': self.unique_users,
            'average_session_duration': round(self.average_session_duration, 2),
            'most_active_user': self.most_active_user,
            'version_breakdown': {k: round(v, 2) for k, v in self.version_breakdown.items()},
            'platform_breakdown': self.platform_breakdown
        }


@dataclass
class RankingResult:
    """
    Represents a ranking result for top N queries.
    
    This model is used for returning ranked lists such as top applications
    by usage time, top users by activity, etc.
    
    Attributes:
        rank (int): Rank position (1-based)
        name (str): Name of the ranked item
        value (Union[int, float]): Value used for ranking
        percentage (float): Percentage of total
        additional_data (Dict[str, Any]): Additional metadata
    """
    
    rank: int
    name: str
    value: Union[int, float]
    percentage: float = 0.0
    additional_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.additional_data is None:
            self.additional_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'rank': self.rank,
            'name': self.name,
            'value': self.value,
            'percentage': round(self.percentage, 2),
            'additional_data': self.additional_data
        }


@dataclass
class SessionData:
    """
    Represents session-based analytics data.
    
    This model is used for session length analysis and related metrics.
    
    Attributes:
        user_id (str): User identifier
        app_name (str): Application name
        session_start (str): Session start timestamp
        session_end (str): Session end timestamp
        duration_minutes (float): Session duration in minutes
        platform (str): Platform used
    """
    
    user_id: str
    app_name: str
    session_start: str
    session_end: str
    duration_minutes: float
    platform: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'user_id': self.user_id,
            'app_name': self.app_name,
            'session_start': self.session_start,
            'session_end': self.session_end,
            'duration_minutes': round(self.duration_minutes, 2),
            'platform': self.platform
        }
