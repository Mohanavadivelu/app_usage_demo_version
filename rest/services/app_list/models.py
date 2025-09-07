"""
Pydantic schemas for App List domain.
"""
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from core.utils import validate_date_format, sanitize_string, parse_boolean

class TrackingConfig(BaseModel):
    """Schema for tracking configuration."""
    usage: bool
    location: bool
    cpu_memory: dict

    @validator('cpu_memory')
    def validate_cpu_memory(cls, v):
        """Validate CPU memory tracking configuration."""
        if not isinstance(v, dict):
            raise ValueError('cpu_memory must be a dictionary')
        
        required_fields = ['track_cm', 'track_intr']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'cpu_memory must contain {field}')
        
        # Validate track_cm is boolean
        v['track_cm'] = parse_boolean(v['track_cm'])
        
        # Validate track_intr is integer
        try:
            v['track_intr'] = int(v['track_intr'])
        except (ValueError, TypeError):
            raise ValueError('track_intr must be an integer')
        
        return v

class AppListBase(BaseModel):
    """Base schema for app list data."""
    app_name: str
    app_type: str
    current_version: str
    released_date: str
    publisher: str
    description: str
    download_link: str
    enable_tracking: bool
    track: TrackingConfig
    registered_date: str

    @validator('app_name')
    def validate_app_name(cls, v):
        """Validate and sanitize app name."""
        return sanitize_string(v, max_length=100)

    @validator('app_type')
    def validate_app_type(cls, v):
        """Validate and sanitize app type."""
        return sanitize_string(v, max_length=50)

    @validator('current_version')
    def validate_current_version(cls, v):
        """Validate and sanitize current version."""
        return sanitize_string(v, max_length=50)

    @validator('released_date')
    def validate_released_date(cls, v):
        """Validate released date format."""
        if not validate_date_format(v):
            raise ValueError('Released date must be in YYYY-MM-DD format')
        return v

    @validator('publisher')
    def validate_publisher(cls, v):
        """Validate and sanitize publisher."""
        return sanitize_string(v, max_length=100)

    @validator('description')
    def validate_description(cls, v):
        """Validate and sanitize description."""
        return sanitize_string(v, max_length=500)

    @validator('download_link')
    def validate_download_link(cls, v):
        """Validate and sanitize download link."""
        sanitized = sanitize_string(v, max_length=500)
        # Basic URL validation
        if not (sanitized.startswith('http://') or sanitized.startswith('https://')):
            raise ValueError('Download link must be a valid URL starting with http:// or https://')
        return sanitized

    @validator('enable_tracking')
    def validate_enable_tracking(cls, v):
        """Validate enable tracking boolean."""
        return parse_boolean(v)

    @validator('registered_date')
    def validate_registered_date(cls, v):
        """Validate registered date format."""
        if not validate_date_format(v):
            raise ValueError('Registered date must be in YYYY-MM-DD format')
        return v

class AppListCreate(AppListBase):
    """Schema for creating new app list entry."""
    pass

class AppListUpdate(BaseModel):
    """Schema for updating app list entry."""
    app_name: Optional[str] = None
    app_type: Optional[str] = None
    current_version: Optional[str] = None
    released_date: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    download_link: Optional[str] = None
    enable_tracking: Optional[bool] = None
    track: Optional[TrackingConfig] = None
    registered_date: Optional[str] = None

    @validator('app_name')
    def validate_app_name(cls, v):
        """Validate and sanitize app name."""
        return sanitize_string(v, max_length=100) if v else v

    @validator('app_type')
    def validate_app_type(cls, v):
        """Validate and sanitize app type."""
        return sanitize_string(v, max_length=50) if v else v

    @validator('current_version')
    def validate_current_version(cls, v):
        """Validate and sanitize current version."""
        return sanitize_string(v, max_length=50) if v else v

    @validator('released_date')
    def validate_released_date(cls, v):
        """Validate released date format."""
        if v and not validate_date_format(v):
            raise ValueError('Released date must be in YYYY-MM-DD format')
        return v

    @validator('publisher')
    def validate_publisher(cls, v):
        """Validate and sanitize publisher."""
        return sanitize_string(v, max_length=100) if v else v

    @validator('description')
    def validate_description(cls, v):
        """Validate and sanitize description."""
        return sanitize_string(v, max_length=500) if v else v

    @validator('download_link')
    def validate_download_link(cls, v):
        """Validate and sanitize download link."""
        if v:
            sanitized = sanitize_string(v, max_length=500)
            if not (sanitized.startswith('http://') or sanitized.startswith('https://')):
                raise ValueError('Download link must be a valid URL starting with http:// or https://')
            return sanitized
        return v

    @validator('enable_tracking')
    def validate_enable_tracking(cls, v):
        """Validate enable tracking boolean."""
        return parse_boolean(v) if v is not None else v

    @validator('registered_date')
    def validate_registered_date(cls, v):
        """Validate registered date format."""
        if v and not validate_date_format(v):
            raise ValueError('Registered date must be in YYYY-MM-DD format')
        return v

class AppList(BaseModel):
    """Schema for returning app list data from the database."""
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

    class Config:
        from_attributes = True

class AppListResponse(AppList):
    """Schema for API response with nested tracking config."""
    track: TrackingConfig

    @classmethod
    def from_db_record(cls, record: dict):
        """Create AppListResponse from database record."""
        track_config = TrackingConfig(
            usage=record['track_usage'],
            location=record['track_location'],
            cpu_memory={
                'track_cm': record['track_cm'],
                'track_intr': record['track_intr']
            }
        )
        
        return cls(
            app_id=record['app_id'],
            app_name=record['app_name'],
            app_type=record['app_type'],
            current_version=record['current_version'],
            released_date=record['released_date'],
            publisher=record['publisher'],
            description=record['description'],
            download_link=record['download_link'],
            enable_tracking=record['enable_tracking'],
            track_usage=record['track_usage'],
            track_location=record['track_location'],
            track_cm=record['track_cm'],
            track_intr=record['track_intr'],
            registered_date=record['registered_date'],
            track=track_config
        )

class AppListListResponse(BaseModel):
    """Schema for returning the app list data list."""
    app_list: List[AppListResponse]
    total: int

class AppListSummary(BaseModel):
    """Schema for app list summary statistics."""
    total_apps: int
    enabled_tracking: int
    disabled_tracking: int
    app_types: dict
    publishers: dict

def flatten_tracking_config(track: TrackingConfig) -> dict:
    """Flatten tracking configuration for database storage."""
    return {
        'track_usage': track.usage,
        'track_location': track.location,
        'track_cm': track.cpu_memory['track_cm'],
        'track_intr': track.cpu_memory['track_intr']
    }
