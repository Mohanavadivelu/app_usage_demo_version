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

# ============================================================================
# SECTION 1: CREATE OPERATIONS
# ============================================================================

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

# ============================================================================
# SECTION 2: READ OPERATIONS
# ============================================================================

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

# ============================================================================
# SECTION 3: UPDATE & DELETE OPERATIONS
# ============================================================================

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

# ============================================================================
# SECTION 4: ANALYTICS OPERATIONS
# ============================================================================

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

# ============================================================================
# SECTION 5: KPI DASHBOARD ANALYTICS OPERATIONS
# ============================================================================

@handle_database_error
def get_active_users_analytics(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get active users count for the specified period."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        if start_date and end_date:
            actual_start = start_date
            actual_end = end_date
        else:
            end_dt = datetime.now()
            if period == "7d":
                start_dt = end_dt - timedelta(days=7)
            elif period == "30d":
                start_dt = end_dt - timedelta(days=30)
            elif period == "90d":
                start_dt = end_dt - timedelta(days=90)
            else:
                start_dt = end_dt - timedelta(days=30)  # default
            
            actual_start = start_dt.strftime('%Y-%m-%d')
            actual_end = end_dt.strftime('%Y-%m-%d')
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get active users count
            cursor.execute('''
                SELECT COUNT(DISTINCT user) as active_users
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
            ''', (actual_start, actual_end))
            
            result = cursor.fetchone()
            active_users = result['active_users'] if result else 0
            
            # Calculate trend (previous period comparison)
            prev_start_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=int(period[:-1]))
            prev_end_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=1)
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user) as prev_active_users
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
            ''', (prev_start_dt.strftime('%Y-%m-%d'), prev_end_dt.strftime('%Y-%m-%d')))
            
            prev_result = cursor.fetchone()
            prev_active_users = prev_result['prev_active_users'] if prev_result else 0
            
            # Calculate trend percentage
            if prev_active_users > 0:
                trend = round(((active_users - prev_active_users) / prev_active_users) * 100, 1)
            else:
                trend = 0.0
            
            logger.info(f"Active users analytics: {active_users} users, {trend}% trend")
            
            return {
                "active_users": active_users,
                "period": period,
                "start_date": actual_start,
                "end_date": actual_end,
                "trend": trend
            }
            
    except Exception as e:
        logger.error(f"Failed to get active users analytics: {e}")
        raise DatabaseError(f"Failed to get active users analytics: {str(e)}")

@handle_database_error
def get_total_hours_analytics(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get total usage hours for the specified period."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        if start_date and end_date:
            actual_start = start_date
            actual_end = end_date
        else:
            end_dt = datetime.now()
            if period == "7d":
                start_dt = end_dt - timedelta(days=7)
            elif period == "30d":
                start_dt = end_dt - timedelta(days=30)
            elif period == "90d":
                start_dt = end_dt - timedelta(days=90)
            else:
                start_dt = end_dt - timedelta(days=30)
            
            actual_start = start_dt.strftime('%Y-%m-%d')
            actual_end = end_dt.strftime('%Y-%m-%d')
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get total hours
            cursor.execute('''
                SELECT COALESCE(SUM(duration_seconds), 0) as total_seconds
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
            ''', (actual_start, actual_end))
            
            result = cursor.fetchone()
            total_seconds = result['total_seconds'] if result else 0
            total_hours = round(total_seconds / 3600, 1)
            total_hours_formatted = seconds_to_duration(total_seconds)
            
            # Get daily breakdown for sparkline
            cursor.execute('''
                SELECT log_date, COALESCE(SUM(duration_seconds), 0) as daily_seconds
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
                GROUP BY log_date
                ORDER BY log_date
            ''', (actual_start, actual_end))
            
            daily_data = cursor.fetchall()
            daily_breakdown = [round(row['daily_seconds'] / 3600, 1) for row in daily_data]
            
            # Calculate trend
            prev_start_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=int(period[:-1]))
            prev_end_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=1)
            
            cursor.execute('''
                SELECT COALESCE(SUM(duration_seconds), 0) as prev_total_seconds
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
            ''', (prev_start_dt.strftime('%Y-%m-%d'), prev_end_dt.strftime('%Y-%m-%d')))
            
            prev_result = cursor.fetchone()
            prev_total_seconds = prev_result['prev_total_seconds'] if prev_result else 0
            
            if prev_total_seconds > 0:
                trend = round(((total_seconds - prev_total_seconds) / prev_total_seconds) * 100, 1)
            else:
                trend = 0.0
            
            logger.info(f"Total hours analytics: {total_hours} hours, {trend}% trend")
            
            return {
                "total_hours": total_hours,
                "total_hours_formatted": total_hours_formatted,
                "period": period,
                "start_date": actual_start,
                "end_date": actual_end,
                "trend": trend,
                "daily_breakdown": daily_breakdown
            }
            
    except Exception as e:
        logger.error(f"Failed to get total hours analytics: {e}")
        raise DatabaseError(f"Failed to get total hours analytics: {str(e)}")

@handle_database_error
def get_new_users_analytics(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get new users count for the specified period."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        if start_date and end_date:
            actual_start = start_date
            actual_end = end_date
        else:
            end_dt = datetime.now()
            if period == "7d":
                start_dt = end_dt - timedelta(days=7)
            elif period == "30d":
                start_dt = end_dt - timedelta(days=30)
            else:
                start_dt = end_dt - timedelta(days=7)  # default to 7d for new users
            
            actual_start = start_dt.strftime('%Y-%m-%d')
            actual_end = end_dt.strftime('%Y-%m-%d')
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get users who first appeared in this period
            cursor.execute('''
                SELECT COUNT(DISTINCT user) as new_users
                FROM app_usage u1
                WHERE u1.log_date BETWEEN ? AND ?
                AND NOT EXISTS (
                    SELECT 1 FROM app_usage u2 
                    WHERE u2.user = u1.user 
                    AND u2.log_date < ?
                )
            ''', (actual_start, actual_end, actual_start))
            
            result = cursor.fetchone()
            new_users = result['new_users'] if result else 0
            
            # Get daily breakdown
            cursor.execute('''
                SELECT u1.log_date, COUNT(DISTINCT u1.user) as daily_new_users
                FROM app_usage u1
                WHERE u1.log_date BETWEEN ? AND ?
                AND NOT EXISTS (
                    SELECT 1 FROM app_usage u2 
                    WHERE u2.user = u1.user 
                    AND u2.log_date < u1.log_date
                )
                GROUP BY u1.log_date
                ORDER BY u1.log_date
            ''', (actual_start, actual_end))
            
            daily_data = cursor.fetchall()
            daily_breakdown = [row['daily_new_users'] for row in daily_data]
            
            # Calculate growth rate (compare with previous period)
            prev_start_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=int(period[:-1]))
            prev_end_dt = datetime.strptime(actual_start, '%Y-%m-%d') - timedelta(days=1)
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user) as prev_new_users
                FROM app_usage u1
                WHERE u1.log_date BETWEEN ? AND ?
                AND NOT EXISTS (
                    SELECT 1 FROM app_usage u2 
                    WHERE u2.user = u1.user 
                    AND u2.log_date < ?
                )
            ''', (prev_start_dt.strftime('%Y-%m-%d'), prev_end_dt.strftime('%Y-%m-%d'), prev_start_dt.strftime('%Y-%m-%d')))
            
            prev_result = cursor.fetchone()
            prev_new_users = prev_result['prev_new_users'] if prev_result else 0
            
            if prev_new_users > 0:
                growth_rate = round(((new_users - prev_new_users) / prev_new_users) * 100, 1)
            else:
                growth_rate = 0.0
            
            logger.info(f"New users analytics: {new_users} users, {growth_rate}% growth")
            
            return {
                "new_users": new_users,
                "period": period,
                "start_date": actual_start,
                "end_date": actual_end,
                "growth_rate": growth_rate,
                "daily_breakdown": daily_breakdown
            }
            
    except Exception as e:
        logger.error(f"Failed to get new users analytics: {e}")
        raise DatabaseError(f"Failed to get new users analytics: {str(e)}")

@handle_database_error
def get_top_app_analytics(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get top application by usage for the specified period."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        if start_date and end_date:
            actual_start = start_date
            actual_end = end_date
        else:
            end_dt = datetime.now()
            if period == "7d":
                start_dt = end_dt - timedelta(days=7)
            elif period == "30d":
                start_dt = end_dt - timedelta(days=30)
            elif period == "90d":
                start_dt = end_dt - timedelta(days=90)
            else:
                start_dt = end_dt - timedelta(days=30)
            
            actual_start = start_dt.strftime('%Y-%m-%d')
            actual_end = end_dt.strftime('%Y-%m-%d')
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get top app by total usage
            cursor.execute('''
                SELECT 
                    application_name,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    COUNT(DISTINCT user) as user_count
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
                GROUP BY application_name
                ORDER BY total_seconds DESC
                LIMIT 1
            ''', (actual_start, actual_end))
            
            result = cursor.fetchone()
            
            if result and result['total_seconds'] > 0:
                app_name = result['application_name']
                total_seconds = result['total_seconds']
                total_hours = round(total_seconds / 3600, 1)
                total_hours_formatted = seconds_to_duration(total_seconds)
                user_count = result['user_count']
                
                # Get daily usage for sparkline
                cursor.execute('''
                    SELECT log_date, COALESCE(SUM(duration_seconds), 0) as daily_seconds
                    FROM app_usage
                    WHERE application_name = ? AND log_date BETWEEN ? AND ?
                    GROUP BY log_date
                    ORDER BY log_date
                ''', (app_name, actual_start, actual_end))
                
                daily_data = cursor.fetchall()
                sparkline_data = [round(row['daily_seconds'] / 3600, 1) for row in daily_data]
                
                logger.info(f"Top app analytics: {app_name} with {total_hours} hours")
                
                return {
                    "app_name": app_name,
                    "total_hours": total_hours,
                    "total_hours_formatted": total_hours_formatted,
                    "user_count": user_count,
                    "period": period,
                    "sparkline_data": sparkline_data
                }
            else:
                return {
                    "app_name": "No data",
                    "total_hours": 0.0,
                    "total_hours_formatted": "00:00:00",
                    "user_count": 0,
                    "period": period,
                    "sparkline_data": []
                }
                
    except Exception as e:
        logger.error(f"Failed to get top app analytics: {e}")
        raise DatabaseError(f"Failed to get top app analytics: {str(e)}")

@handle_database_error
def get_churn_rate_analytics(period: str, cohort_period: str) -> Dict[str, Any]:
    """Get user churn rate for the specified period."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate cohort dates
        end_dt = datetime.now()
        if cohort_period == "30d":
            cohort_start_dt = end_dt - timedelta(days=60)  # Look at users from 60 days ago
            cohort_end_dt = end_dt - timedelta(days=30)    # Who were active 30 days ago
        elif cohort_period == "90d":
            cohort_start_dt = end_dt - timedelta(days=180)
            cohort_end_dt = end_dt - timedelta(days=90)
        else:
            cohort_start_dt = end_dt - timedelta(days=60)
            cohort_end_dt = end_dt - timedelta(days=30)
        
        # Recent activity period
        if period == "30d":
            recent_start_dt = end_dt - timedelta(days=30)
        elif period == "90d":
            recent_start_dt = end_dt - timedelta(days=90)
        else:
            recent_start_dt = end_dt - timedelta(days=30)
        
        cohort_start = cohort_start_dt.strftime('%Y-%m-%d')
        cohort_end = cohort_end_dt.strftime('%Y-%m-%d')
        recent_start = recent_start_dt.strftime('%Y-%m-%d')
        recent_end = end_dt.strftime('%Y-%m-%d')
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get users who were active in the cohort period
            cursor.execute('''
                SELECT COUNT(DISTINCT user) as cohort_users
                FROM app_usage
                WHERE log_date BETWEEN ? AND ?
            ''', (cohort_start, cohort_end))
            
            cohort_result = cursor.fetchone()
            total_users = cohort_result['cohort_users'] if cohort_result else 0
            
            if total_users == 0:
                return {
                    "churn_rate": 0.0,
                    "period": period,
                    "total_users": 0,
                    "churned_users": 0,
                    "status": "no_data"
                }
            
            # Get users from cohort who are still active recently
            cursor.execute('''
                SELECT COUNT(DISTINCT u1.user) as retained_users
                FROM app_usage u1
                WHERE u1.log_date BETWEEN ? AND ?
                AND EXISTS (
                    SELECT 1 FROM app_usage u2
                    WHERE u2.user = u1.user
                    AND u2.log_date BETWEEN ? AND ?
                )
            ''', (cohort_start, cohort_end, recent_start, recent_end))
            
            retained_result = cursor.fetchone()
            retained_users = retained_result['retained_users'] if retained_result else 0
            
            churned_users = total_users - retained_users
            churn_rate = round((churned_users / total_users) * 100, 1) if total_users > 0 else 0.0
            
            # Determine health status
            if churn_rate <= 5.0:
                status = "healthy"
            elif churn_rate <= 15.0:
                status = "warning"
            else:
                status = "critical"
            
            logger.info(f"Churn rate analytics: {churn_rate}% ({churned_users}/{total_users}), status: {status}")
            
            return {
                "churn_rate": churn_rate,
                "period": period,
                "total_users": total_users,
                "churned_users": churned_users,
                "status": status
            }
            
    except Exception as e:
        logger.error(f"Failed to get churn rate analytics: {e}")
        raise DatabaseError(f"Failed to get churn rate analytics: {str(e)}")

@handle_database_error
def get_dashboard_summary_analytics(period: str) -> Dict[str, Any]:
    """Get comprehensive dashboard summary with all KPI metrics."""
    try:
        # Get all analytics in one call for efficiency
        active_users = get_active_users_analytics(period)
        total_hours = get_total_hours_analytics(period)
        new_users = get_new_users_analytics("7d")  # Always show 7d for new users
        top_app = get_top_app_analytics(period)
        churn_rate = get_churn_rate_analytics(period, "30d")
        
        # Get total apps from app_list (if available)
        try:
            with get_db_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as total_apps FROM app_list")
                app_result = cursor.fetchone()
                total_apps = app_result['total_apps'] if app_result else 0
        except:
            total_apps = 0
        
        logger.info(f"Dashboard summary generated for period: {period}")
        
        return {
            "period": period,
            "total_apps": total_apps,
            "active_users": active_users,
            "total_hours": total_hours,
            "new_users": new_users,
            "top_app": top_app,
            "churn_rate": churn_rate,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise DatabaseError(f"Failed to get dashboard summary: {str(e)}")

# ============================================================================
# SECTION 6: UTILITY FUNCTIONS
# ============================================================================

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
