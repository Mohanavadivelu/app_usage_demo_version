"""
FastAPI routes for App List service.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from core.auth import get_api_key
from core.exceptions import ApplicationError, NotFoundError, ValidationError, log_error
from .models import (
    AppListResponse, AppListCreate, AppListUpdate, AppListListResponse, 
    AppListSummary
)
from . import crud, database

logger = logging.getLogger(__name__)

# Initialize the database (creates table if not exists)
try:
    database.init_db()
    logger.info("App list database initialized")
except Exception as e:
    logger.error(f"Failed to initialize app list database: {e}")
    raise

# APIRouter for app list endpoints
router = APIRouter(prefix="/app_list", tags=["App List"])

# ============================================================================
# SECTION 1: CREATE ENDPOINTS
# ============================================================================

@router.post("/", response_model=int, dependencies=[Depends(get_api_key)])
def create_app_list_entry(app_list: AppListCreate):
    """
    Create new app list entry.

    Example:
        curl -X POST "http://localhost:8000/api/v1/app_list/" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{
            "app_name": "notepad",
            "app_type": "windows",
            "current_version": "1.0.0",
            "released_date": "2025-01-01",
            "publisher": "Microsoft",
            "description": "Simple text editor",
            "download_link": "https://microsoft.com/notepad",
            "enable_tracking": true,
            "track": {
                "usage": true,
                "location": false,
                "cpu_memory": {
                    "track_cm": false,
                    "track_intr": 1
                }
            },
            "registered_date": "2025-01-07"
        }'
    """
    try:
        logger.info(f"Creating app list entry for: {app_list.app_name}")

        # Create the record
        record_id = crud.create_app_list(app_list)

        logger.info(f"Successfully created app list entry - Record ID: {record_id}")
        return record_id

    except ValidationError as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "create_app_list"})
        raise HTTPException(status_code=400, detail=str(e))
    except ApplicationError as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "create_app_list"})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "create_app_list"})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upsert", response_model=int, dependencies=[Depends(get_api_key)])
def create_or_update_app_list_entry(app_list: AppListCreate):
    """
    Create new app list entry or update existing one.
    If an entry exists with the same app_name, app_type, and current_version,
    it will be updated. Otherwise, a new entry is created.

    Example:
        curl -X POST "http://localhost:8000/api/v1/app_list/upsert" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{
            "app_name": "notepad",
            "app_type": "windows",
            "current_version": "1.0.0",
            "released_date": "2025-01-01",
            "publisher": "Microsoft",
            "description": "Simple text editor",
            "download_link": "https://microsoft.com/notepad",
            "enable_tracking": true,
            "track": {
                "usage": true,
                "location": false,
                "cpu_memory": {
                    "track_cm": false,
                    "track_intr": 1
                }
            },
            "registered_date": "2025-01-07"
        }'
    """
    try:
        logger.info(f"Creating/updating app list entry for: {app_list.app_name}")

        # Process the data
        record_id = crud.create_or_update_app_list(app_list)

        logger.info(f"Successfully processed app list entry - Record ID: {record_id}")
        return record_id

    except ValidationError as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "upsert_app_list"})
        raise HTTPException(status_code=400, detail=str(e))
    except ApplicationError as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "upsert_app_list"})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"app_name": app_list.app_name, "operation": "upsert_app_list"})
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# SECTION 2: READ ENDPOINTS
# ============================================================================

@router.get("/", response_model=AppListListResponse, dependencies=[Depends(get_api_key)])
def list_app_list_entries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List all app list entries with pagination.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_list/?skip=0&limit=10" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        result = crud.get_app_list(skip=skip, limit=limit)
        
        # Convert to response format with nested tracking config
        app_list_responses = [
            AppListResponse.from_db_record(record) 
            for record in result["app_list"]
        ]
        
        return {
            "app_list": app_list_responses,
            "total": result["total"]
        }
    except Exception as e:
        log_error(e, {"operation": "list_app_list", "skip": skip, "limit": limit})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{app_id}", response_model=AppListResponse, dependencies=[Depends(get_api_key)])
def get_app_list_entry(app_id: int):
    """
    Get a specific app list entry by ID.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_list/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        record = crud.get_app_list_by_id(app_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"App list entry not found (ID: {app_id})")
        
        return AppListResponse.from_db_record(record)
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"operation": "get_app_list", "app_id": app_id})
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# SECTION 3: UPDATE & DELETE ENDPOINTS
# ============================================================================

@router.put("/{app_id}", response_model=bool, dependencies=[Depends(get_api_key)])
def update_app_list_entry(app_id: int, app_list_update: AppListUpdate):
    """
    Update an existing app list entry.
    
    Example:
        curl -X PUT "http://localhost:8000/api/v1/app_list/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
        -H "Content-Type: application/json" \
        -d '{"description": "Updated description", "enable_tracking": false}'
    """
    try:
        success = crud.update_app_list(app_id, app_list_update)
        if not success:
            raise HTTPException(status_code=404, detail=f"App list entry not found (ID: {app_id})")
        return success
    except HTTPException:
        raise
    except ValidationError as e:
        log_error(e, {"operation": "update_app_list", "app_id": app_id})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(e, {"operation": "update_app_list", "app_id": app_id})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{app_id}", response_model=bool, dependencies=[Depends(get_api_key)])
def delete_app_list_entry(app_id: int):
    """
    Delete an app list entry.
    
    Example:
        curl -X DELETE "http://localhost:8000/api/v1/app_list/1" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        success = crud.delete_app_list(app_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"App list entry not found (ID: {app_id})")
        return success
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"operation": "delete_app_list", "app_id": app_id})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/by-name/{app_name}", response_model=List[AppListResponse], dependencies=[Depends(get_api_key)])
def get_app_list_by_name(app_name: str):
    """
    Get app list entries by app name.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_list/by-name/notepad" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        records = crud.get_app_list_by_name(app_name)
        return [AppListResponse.from_db_record(record) for record in records]
    except Exception as e:
        log_error(e, {"operation": "get_app_list_by_name", "app_name": app_name})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/by-type/{app_type}", response_model=List[AppListResponse], dependencies=[Depends(get_api_key)])
def get_app_list_by_type(app_type: str):
    """
    Get app list entries by app type.
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_list/by-type/windows" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        records = crud.get_app_list_by_type(app_type)
        return [AppListResponse.from_db_record(record) for record in records]
    except Exception as e:
        log_error(e, {"operation": "get_app_list_by_type", "app_type": app_type})
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary/stats", response_model=AppListSummary, dependencies=[Depends(get_api_key)])
def get_app_list_summary():
    """
    Get summary statistics for app list.
    
    Returns:
        - total_apps: Total number of apps
        - enabled_tracking: Number of apps with tracking enabled
        - disabled_tracking: Number of apps with tracking disabled
        - app_types: Distribution of app types
        - publishers: Top publishers by app count
    
    Example:
        curl -X GET "http://localhost:8000/api/v1/app_list/summary/stats" \
        -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
    """
    try:
        summary = crud.get_app_list_summary()
        return summary
    except Exception as e:
        log_error(e, {"operation": "get_app_list_summary"})
        raise HTTPException(status_code=500, detail="Internal server error")
