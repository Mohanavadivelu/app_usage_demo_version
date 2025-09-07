"""
Pydantic schemas for App Usage domain.
"""
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from core.utils import duration_to_seconds, seconds_to_duration

class AppUsageBase(BaseModel):
    """Base schema for app usage data."""
    monitor_app_version: str  # Version of the monitoring application
    platform: str  # Operating system (e.g., "windows")
    user: str  # Username
    application_name: str  # Name of the tracked application
    application_version: str  # Version of the tracked application
    log_date: str  # Date when usage was recorded (YYYY-MM-DD format)
    legacy_app: bool  # Boolean indicating if it's a legacy application
    duration: str  # Time duration in HH:MM:SS format (API interface)

    @validator('monitor_app_version')
    def validate_monitor_app_version(cls, v):
        """Validate monitor app version length."""
        if len(v) > 50:
            raise ValueError('Monitor app version must be 50 characters or less')
        return v.strip()

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform length."""
        if len(v) > 50:
            raise ValueError('Platform must be 50 characters or less')
        return v.strip()

    @validator('user')
    def validate_user(cls, v):
        """Validate user length."""
        if len(v) > 100:
            raise ValueError('User must be 100 characters or less')
        return v.strip()

    @validator('application_name')
    def validate_application_name(cls, v):
        """Validate application name length."""
        if len(v) > 100:
            raise ValueError('Application name must be 100 characters or less')
        return v.strip()

    @validator('application_version')
    def validate_application_version(cls, v):
        """Validate application version length."""
        if len(v) > 50:
            raise ValueError('Application version must be 50 characters or less')
        return v.strip()

    @validator('log_date')
    def validate_log_date(cls, v):
        """Validate log date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Log date must be in YYYY-MM-DD format')
        return v

    @validator('duration')
    def validate_duration_format(cls, v):
        """Validate that duration is in HH:MM:SS format."""
        # Use the conversion function which includes validation
        duration_to_seconds(v)  # This will raise ValueError if invalid
        return v

class AppUsageCreate(AppUsageBase):
    """Schema for creating new app usage data."""
    pass

class AppUsageUpdate(BaseModel):
    """Schema for updating app usage data."""
    monitor_app_version: Optional[str] = None
    platform: Optional[str] = None
    user: Optional[str] = None
    application_name: Optional[str] = None
    application_version: Optional[str] = None
    log_date: Optional[str] = None
    legacy_app: Optional[bool] = None
    duration: Optional[str] = None

    @validator('monitor_app_version')
    def validate_monitor_app_version(cls, v):
        """Validate monitor app version length."""
        if v is not None and len(v) > 50:
            raise ValueError('Monitor app version must be 50 characters or less')
        return v.strip() if v else v

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform length."""
        if v is not None and len(v) > 50:
            raise ValueError('Platform must be 50 characters or less')
        return v.strip() if v else v

    @validator('user')
    def validate_user(cls, v):
        """Validate user length."""
        if v is not None and len(v) > 100:
            raise ValueError('User must be 100 characters or less')
        return v.strip() if v else v

    @validator('application_name')
    def validate_application_name(cls, v):
        """Validate application name length."""
        if v is not None and len(v) > 100:
            raise ValueError('Application name must be 100 characters or less')
        return v.strip() if v else v

    @validator('application_version')
    def validate_application_version(cls, v):
        """Validate application version length."""
        if v is not None and len(v) > 50:
            raise ValueError('Application version must be 50 characters or less')
        return v.strip() if v else v

    @validator('log_date')
    def validate_log_date(cls, v):
        """Validate log date format."""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Log date must be in YYYY-MM-DD format')
        return v

    @validator('duration')
    def validate_duration_format(cls, v):
        """Validate that duration is in HH:MM:SS format."""
        if v is not None:
            duration_to_seconds(v)  # This will raise ValueError if invalid
        return v

class AppUsage(AppUsageBase):
    """Schema for returning app usage data from the database."""
    id: int  # Unique identifier for the usage data
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enable from_attributes mode for compatibility with DB models

class AppUsageListResponse(BaseModel):
    """Schema for returning the app usage data list."""
    app_usage: List[AppUsage]
    total: int

class AppUsageAnalytics(BaseModel):
    """Schema for application usage analytics."""
    application: str
    user_count: int
    total_hours: str  # HH:MM:SS format
    total_records: int

class AppUsageAnalyticsWithDateRange(BaseModel):
    """Schema for application usage analytics with date range."""
    application: str
    user_count: int
    total_hours: str  # HH:MM:SS format
    total_records: int
    start_date: str
    end_date: str

class UserUsageAnalytics(BaseModel):
    """Schema for user-specific usage analytics."""
    user: str
    total_applications: int
    total_hours: str  # HH:MM:SS format
    total_records: int

def add_durations(duration1: str, duration2: str) -> str:
    """Add two HH:MM:SS duration strings and return the sum as HH:MM:SS."""
    try:
        # Convert to seconds, add, then convert back
        seconds1 = duration_to_seconds(duration1)
        seconds2 = duration_to_seconds(duration2)
        total_seconds = seconds1 + seconds2
        return seconds_to_duration(total_seconds)
    except (ValueError, AttributeError):
        raise ValueError('Both durations must be in HH:MM:SS format')
