"""
CRUD operations for App Usage domain.
"""
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from core.database import get_db_transaction, get_db_context
from core.exceptions import DatabaseError, NotFoundError, handle_database_error
from core.utils import duration_to_seconds, seconds_to_duration
from .models import AppUsageCreate, AppUsageUpdate, AppUsage

logger = logging.getLogger(__name__)

@handle_database_error
def create_app_usage(app_usage: AppUsageCreate) -> int:
    """
    Create new app usage record.
    Returns the ID of the created record.
    """
    try:
        # Log the received data
        logger.info(f"Creating app usage for user: {app_usage.user}, app: {app_usage.application_name}")
        logger.debug(f"App usage details: {json.dumps(app_usage.dict(), indent=2)}")

        # Convert duration to seconds for storage
        duration_seconds = duration_to_seconds(app_usage.duration)

        with get_db_transaction() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO app_usage
                (monitor_app_version, platform, user, application_name,
                 application_version, log_date, legacy_app, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_usage.monitor_app_version, app_usage.platform, app_usage.user,
                app_usage.application_name, app_usage.application_version,
                app_usage.log_date, app_usage.legacy_app, duration_seconds
            ))

            record_id = cursor.lastrowid
            logger.info(f"Successfully created app usage record (ID: {record_id})")
            return record_id

    except Exception as e:
        logger.error(f"Failed to create app usage for user {app_usage.user}, app {app_usage.application_name}: {e}")
        raise DatabaseError(f"Failed to create app usage: {str(e)}")

@handle_database_error
def create_or_update_app_usage(app_usage: AppUsageCreate) -> int:
    """
    Create new app usage or update existing record by summing durations.
    If a record exists with the same user, application_name, and log_date,
    the durations are summed. Otherwise, a new record is created.
    Returns the ID of the created or updated record.
    """
    try:
        # Log the received data
        logger.info(f"Processing app usage for user: {app_usage.user}, app: {app_usage.application_name}")
        logger.debug(f"App usage details: {json.dumps(app_usage.dict(), indent=2)}")

        # Convert duration to seconds for storage
        new_duration_seconds = duration_to_seconds(app_usage.duration)

        with get_db_transaction() as conn:
            cursor = conn.cursor()

            # Check if a record exists with the same user, application_name, and log_date
            cursor.execute('''
                SELECT id, duration_seconds FROM app_usage
                WHERE user = ? AND application_name = ? AND log_date = ?
            ''', (app_usage.user, app_usage.application_name, app_usage.log_date))

            existing_record = cursor.fetchone()

            if existing_record:
                # Update existing record by summing durations
                record_id = existing_record['id']
                current_duration_seconds = existing_record['duration_seconds']
                total_duration_seconds = current_duration_seconds + new_duration_seconds

                # Convert back to HH:MM:SS for logging
                current_duration_str = seconds_to_duration(current_duration_seconds)
                total_duration_str = seconds_to_duration(total_duration_seconds)

                logger.info(f"Updating existing record (ID: {record_id})")
                logger.debug(f"Previous duration: {current_duration_str}, Adding: {app_usage.duration}, New total: {total_duration_str}")

                cursor.execute('''
                    UPDATE app_usage SET
                    monitor_app_version = ?, platform = ?, application_version = ?,
                    legacy_app = ?, duration_seconds = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    app_usage.monitor_app_version, app_usage.platform,
                    app_usage.application_version, app_usage.legacy_app,
                    total_duration_seconds, record_id
                ))

                logger.info(f"Successfully updated app usage record (ID: {record_id})")
                return record_id
            else:
                # Create new record
                logger.info(f"Creating new app usage record")
                logger.debug(f"Duration: {app_usage.duration}")

                cursor.execute('''
                    INSERT INTO app_usage
                    (monitor_app_version, platform, user, application_name,
                     application_version, log_date, legacy_app, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app_usage.monitor_app_version, app_usage.platform, app_usage.user,
                    app_usage.application_name, app_usage.application_version,
                    app_usage.log_date, app_usage.legacy_app, new_duration_seconds
                ))

                record_id = cursor.lastrowid
                logger.info(f"Successfully created new app usage record (ID: {record_id})")
                return record_id

    except Exception as e:
        logger.error(f"Failed to create/update app usage for user {app_usage.user}, app {app_usage.application_name}: {e}")
        raise DatabaseError(f"Failed to create/update app usage: {str(e)}")

@handle_database_error
def get_app_usage_by_id(usage_id: int) -> Optional[Dict[str, Any]]:
    """Get app usage record by ID."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_usage WHERE id = ?", (usage_id,))
            row = cursor.fetchone()

            if row:
                data = _row_to_dict(row)
                logger.info(f"Retrieved app usage record (ID: {usage_id})")
                return data
            else:
                logger.info(f"App usage record not found (ID: {usage_id})")
                return None

    except Exception as e:
        logger.error(f"Failed to retrieve app usage record (ID: {usage_id}): {e}")
        raise DatabaseError(f"Failed to retrieve app usage record: {str(e)}")

@handle_database_error
def get_app_usage_list(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Retrieve app usage data as a list with pagination."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM app_usage")
            total = cursor.fetchone()['total']
            
            # Get paginated data
            cursor.execute("""
                SELECT * FROM app_usage 
                ORDER BY log_date DESC, id DESC 
                LIMIT ? OFFSET ?
            """, (limit, skip))
            rows = cursor.fetchall()

            data = [_row_to_dict(row) for row in rows]
            logger.info(f"Retrieved {len(data)} app usage records (total: {total})")
            
            return {
                "app_usage": data,
                "total": total
            }

    except Exception as e:
        logger.error(f"Failed to retrieve app usage list: {e}")
        raise DatabaseError(f"Failed to retrieve app usage list: {str(e)}")

@handle_database_error
def update_app_usage(usage_id: int, app_usage_update: AppUsageUpdate) -> bool:
    """Update app usage record."""
    try:
        # Get current record
        current_record = get_app_usage_by_id(usage_id)
        if not current_record:
            raise NotFoundError(f"App usage record not found (ID: {usage_id})")

        # Build update query dynamically
        update_fields = []
        update_values = []
        
        for field, value in app_usage_update.dict(exclude_unset=True).items():
            if field == 'duration' and value is not None:
                # Convert duration to seconds
                update_fields.append('duration_seconds = ?')
                update_values.append(duration_to_seconds(value))
            elif value is not None:
                update_fields.append(f'{field} = ?')
                update_values.append(value)
        
        if not update_fields:
            logger.info(f"No fields to update for app usage record (ID: {usage_id})")
            return True

        # Add updated_at timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        update_values.append(usage_id)

        with get_db_transaction() as conn:
            cursor = conn.cursor()
            query = f"UPDATE app_usage SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                logger.info(f"Successfully updated app usage record (ID: {usage_id})")
                return True
            else:
                logger.warning(f"No rows updated for app usage record (ID: {usage_id})")
                return False

    except Exception as e:
        logger.error(f"Failed to update app usage record (ID: {usage_id}): {e}")
        raise DatabaseError(f"Failed to update app usage record: {str(e)}")

@handle_database_error
def delete_app_usage(usage_id: int) -> bool:
    """Delete app usage record."""
    try:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_usage WHERE id = ?", (usage_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Successfully deleted app usage record (ID: {usage_id})")
                return True
            else:
                logger.warning(f"App usage record not found for deletion (ID: {usage_id})")
                return False

    except Exception as e:
        logger.error(f"Failed to delete app usage record (ID: {usage_id}): {e}")
        raise DatabaseError(f"Failed to delete app usage record: {str(e)}")

@handle_database_error
def get_application_analytics(application_name: str) -> Dict[str, Any]:
    """Get user count and total hours for a specific application."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # Get user count, total duration in seconds, and record count
            cursor.execute('''
                SELECT
                    COUNT(DISTINCT user) as user_count,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    COUNT(*) as total_records
                FROM app_usage
                WHERE application_name = ?
            ''', (application_name,))

            result = cursor.fetchone()

            if result and result['user_count'] > 0:
                total_hours = seconds_to_duration(result['total_seconds'])
                logger.info(f"Retrieved analytics for {application_name}: {result['user_count']} users, {total_hours} total")
                return {
                    "application": application_name,
                    "user_count": result['user_count'],
                    "total_hours": total_hours,
                    "total_records": result['total_records']
                }
            else:
                logger.info(f"No analytics data found for {application_name}")
                return {
                    "application": application_name,
                    "user_count": 0,
                    "total_hours": "00:00:00",
                    "total_records": 0
                }

    except Exception as e:
        logger.error(f"Failed to get analytics for {application_name}: {e}")
        raise DatabaseError(f"Failed to get analytics for {application_name}: {str(e)}")

@handle_database_error
def get_application_analytics_by_date_range(application_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get user count and total hours for a specific application within date range."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # Get user count, total duration in seconds, and record count for date range
            cursor.execute('''
                SELECT
                    COUNT(DISTINCT user) as user_count,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    COUNT(*) as total_records
                FROM app_usage
                WHERE application_name = ?
                AND log_date BETWEEN ? AND ?
            ''', (application_name, start_date, end_date))

            result = cursor.fetchone()

            if result and result['user_count'] > 0:
                total_hours = seconds_to_duration(result['total_seconds'])
                logger.info(f"Retrieved analytics for {application_name} ({start_date} to {end_date}): {result['user_count']} users, {total_hours} total")
                return {
                    "application": application_name,
                    "user_count": result['user_count'],
                    "total_hours": total_hours,
                    "total_records": result['total_records'],
                    "start_date": start_date,
                    "end_date": end_date
                }
            else:
                logger.info(f"No analytics data found for {application_name} in date range {start_date} to {end_date}")
                return {
                    "application": application_name,
                    "user_count": 0,
                    "total_hours": "00:00:00",
                    "total_records": 0,
                    "start_date": start_date,
                    "end_date": end_date
                }

    except Exception as e:
        logger.error(f"Failed to get analytics for {application_name} in date range {start_date} to {end_date}: {e}")
        raise DatabaseError(f"Failed to get analytics for {application_name} in date range: {str(e)}")

@handle_database_error
def get_user_analytics(user: str) -> Dict[str, Any]:
    """Get analytics for a specific user."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # Get application count, total duration in seconds, and record count
            cursor.execute('''
                SELECT
                    COUNT(DISTINCT application_name) as total_applications,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    COUNT(*) as total_records
                FROM app_usage
                WHERE user = ?
            ''', (user,))

            result = cursor.fetchone()

            if result and result['total_applications'] > 0:
                total_hours = seconds_to_duration(result['total_seconds'])
                logger.info(f"Retrieved analytics for user {user}: {result['total_applications']} apps, {total_hours} total")
                return {
                    "user": user,
                    "total_applications": result['total_applications'],
                    "total_hours": total_hours,
                    "total_records": result['total_records']
                }
            else:
                logger.info(f"No analytics data found for user {user}")
                return {
                    "user": user,
                    "total_applications": 0,
                    "total_hours": "00:00:00",
                    "total_records": 0
                }

    except Exception as e:
        logger.error(f"Failed to get analytics for user {user}: {e}")
        raise DatabaseError(f"Failed to get analytics for user {user}: {str(e)}")

def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a database row to the expected dictionary format."""
    # Convert duration_seconds back to HH:MM:SS for API response
    duration_str = seconds_to_duration(row["duration_seconds"])
    
    return {
        "id": row["id"],
        "monitor_app_version": row["monitor_app_version"],
        "platform": row["platform"],
        "user": row["user"],
        "application_name": row["application_name"],
        "application_version": row["application_version"],
        "log_date": row["log_date"],
        "legacy_app": bool(row["legacy_app"]),
        "duration": duration_str,  # Convert back to HH:MM:SS for API
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at")
    }
