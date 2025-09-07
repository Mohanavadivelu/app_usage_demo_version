"""
FastAPI routes for App Usage service.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from core.auth import get_api_key
from core.exceptions import ApplicationError, NotFoundError, ValidationError, log_error
from .models import (
    AppUsage, AppUsageCreate, AppUsageUpdate, AppUsageListResponse, 
    AppUsageAnalytics, AppUsageAnalyticsWithDateRange, UserUsageAnalytics
)
from . import crud, database

logger = logging.getLogger(__name__)

# Initialize the database (creates table if not exists)
try:
    database.init_db()
    logger.info("App usage database initialized")
except Exception as e:
    logger.error(f"Failed to initialize app usage database: {e}")
    raise

# APIRouter for app usage endpoints
router = APIRouter(prefix="/app_usage", tags=["App Usage"])

@router.post("/", response_model=int, dependencies=[Depends(get_api_key)])
def create_app_usage_record(app_usage: AppUsageCreate):
    """
    Create new app usage record.

    Example:
        curl -X POST "http://localhost:8000/api/v1/app_usage/" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{
            "monitor_app_version": "1.0.1",
            "platform": "windows",
            "user": "vroot",
            "application_name": "chrome",
            "application_version": "138.0.7204.97",
            "log_date": "2025-01-07",
            "legacy_app": true,
            "duration": "00:00:13"
        }'
    """
    try:
        logger.info(f"Creating app usage for user: {app_usage.user}, app: {app_usage.application_name}")

        # Create the record
        record_id = crud.create_app_usage(app_usage)

        logger.info(f"Successfully created app usage record - Record ID: {record_id}")
        return record_id

    except ValidationError as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "create_app_usage"})
        raise HTTPException(status_code=400, detail=str(e))
    except ApplicationError as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "create_app_usage"})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "create_app_usage"})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upsert", response_model=int, dependencies=[Depends(get_api_key)])
def create_or_update_app_usage_record(app_usage: AppUsageCreate):
    """
    Create new app usage or update existing record by summing durations.
    If a record exists with the same user, application_name, and log_date,
    the durations are summed. Otherwise, a new record is created.

    Example:
        curl -X POST "http://localhost:8000/api/v1/app_usage/upsert" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{
            "monitor_app_version": "1.0.1",
            "platform": "windows",
            "user": "vroot",
            "application_name": "chrome",
            "application_version": "138.0.7204.97",
            "log_date": "2025-01-07",
            "legacy_app": true,
            "duration": "00:00:13"
        }'
    """
    try:
        logger.info(f"Creating/updating app usage for user: {app_usage.user}, app: {app_usage.application_name}")

        # Process the data
        record_id = crud.create_or_update_app_usage(app_usage)

        logger.info(f"Successfully processed app usage - Record ID: {record_id}")
        return record_id

    except ValidationError as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "upsert_app_usage"})
        raise HTTPException(status_code=400, detail=str(e))
    except ApplicationError as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "upsert_app_usage"})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"user": app_usage.user, "app": app_usage.application_name, "operation": "upsert_app_usage"})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=AppUsageListResponse, dependencies=[Depends(get_api_key)])
def list_app_usage_records(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List all app usage records with pagination.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_usage/?skip=0&limit=10" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        result = crud.get_app_usage_list(skip=skip, limit=limit)
        return result
    except Exception as e:
        log_error(e, {"operation": "list_app_usage", "skip": skip, "limit": limit})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{usage_id}", response_model=AppUsage, dependencies=[Depends(get_api_key)])
def get_app_usage_record(usage_id: int):
    """
    Get a specific app usage record by ID.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_usage/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        record = crud.get_app_usage_by_id(usage_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"App usage record not found (ID: {usage_id})")
        return record
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"operation": "get_app_usage", "usage_id": usage_id})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{usage_id}", response_model=bool, dependencies=[Depends(get_api_key)])
def update_app_usage_record(usage_id: int, app_usage_update: AppUsageUpdate):
    """
    Update an existing app usage record.
    
    Example:
        curl -X PUT "http://localhost:8000/api/v1/app_usage/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{"duration": "00:01:30"}'
    """
    try:
        success = crud.update_app_usage(usage_id, app_usage_update)
        if not success:
            raise HTTPException(status_code=404, detail=f"App usage record not found (ID: {usage_id})")
        return success
    except HTTPException:
        raise
    except ValidationError as e:
        log_error(e, {"operation": "update_app_usage", "usage_id": usage_id})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"operation": "update_app_usage", "usage_id": usage_id})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{usage_id}", response_model=bool, dependencies=[Depends(get_api_key)])
def delete_app_usage_record(usage_id: int):
    """
    Delete an app usage record.
    
    Example:
        curl -X DELETE "http://localhost:8000/api/v1/app_usage/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        success = crud.delete_app_usage(usage_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"App usage record not found (ID: {usage_id})")
        return success
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"operation": "delete_app_usage", "usage_id": usage_id})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/{application_name}", response_model=AppUsageAnalytics, dependencies=[Depends(get_api_key)])
def get_application_analytics(application_name: str):
    """
    Get analytics for a specific application: user count, total usage hours, and record count.
    
    Args:
        application_name: Name of the application (e.g., "chrome", "code")
    
    Returns:
        - application: Application name
        - user_count: Number of unique users
        - total_hours: Total usage time in HH:MM:SS format
        - total_records: Total number of usage records
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_usage/analytics/chrome" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        analytics = crud.get_application_analytics(application_name)
        return analytics
    except Exception as e:
        log_error(e, {"operation": "get_application_analytics", "application": application_name})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/{application_name}/date-range", response_model=AppUsageAnalyticsWithDateRange, dependencies=[Depends(get_api_key)])
def get_application_analytics_by_date_range(
    application_name: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """
    Get analytics for a specific application within a date range.
    
    Args:
        application_name: Name of the application (e.g., "chrome", "code")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        - application: Application name
        - user_count: Number of unique users in the date range
        - total_hours: Total usage time in HH:MM:SS format
        - total_records: Total number of usage records
        - start_date: Start date of the range
        - end_date: End date of the range
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_usage/analytics/chrome/date-range?start_date=2025-01-01&end_date=2025-01-31" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    # Validate date format (basic validation)
    try:
        from datetime import datetime
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    
    try:
        analytics = crud.get_application_analytics_by_date_range(application_name, start_date, end_date)
        return analytics
    except Exception as e:
        log_error(e, {"operation": "get_application_analytics_date_range", "application": application_name, "start_date": start_date, "end_date": end_date})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user-analytics/{user}", response_model=UserUsageAnalytics, dependencies=[Depends(get_api_key)])
def get_user_analytics(user: str):
    """
    Get analytics for a specific user: application count, total usage hours, and record count.
    
    Args:
        user: Username
    
    Returns:
        - user: Username
        - total_applications: Number of unique applications used
        - total_hours: Total usage time in HH:MM:SS format
        - total_records: Total number of usage records
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_usage/user-analytics/vroot" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        analytics = crud.get_user_analytics(user)
        return analytics
    except Exception as e:
        log_error(e, {"operation": "get_user_analytics", "user": user})
        raise HTTPException(status_code=500, detail="Internal server error")
